import streamlit as st
import pandas as pd


def render_analytics_page(spots_df, reservations_df):
    st.header("📊 Analytics Dashboard")

    total_spots = len(spots_df)
    reserved_spots = len(spots_df[spots_df['status'] == 'reserved'])
    available_spots = len(spots_df[spots_df['status'] == 'available'])

    col1, col2, col3 = st.columns(3)
    col1.metric("🅿️ Total Spots", total_spots)
    col2.metric("🟡 Reserved", reserved_spots)
    col3.metric("🟢 Available", available_spots)

    st.markdown("---")
    st.subheader("📋 Reservation History")
    st.dataframe(reservations_df.sort_values("created_at", ascending=False))


def render_system_settings_page(db):
    st.header("🔧 System Settings")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Reset Parking Spots"):
            db.initialize_parking_spots()
            st.success("Parking spots have been reset.")
            st.rerun()

    with col2:
        if st.button("🧹 Clear Reservation History"):
            empty_df = pd.DataFrame(columns=[
                'id', 'spot_id', 'plate_number', 'customer_name', 'customer_email',
                'customer_phone', 'start_time', 'end_time', 'duration_minutes',
                'status', 'created_at'
            ])
            empty_df.to_csv(db.reservations_file, index=False)
            st.success("Reservation history cleared.")
            st.rerun()

def render_user_admin_panel():

    from user import UserDatabase
    st.subheader("👥 User Accounts")

    db = UserDatabase()
    users_df = db.load_users()
    st.dataframe(users_df)

    if st.button("🔄 Refresh User List"):
        st.rerun()
def render_user_passwords_view():
    from user import UserDatabase
    st.subheader("🔑 View User Passwords")

    master_key = st.text_input("Enter admin password to reveal users' passwords", type="password")
    if master_key == "papitxo":
        db = UserDatabase()
        df = db.load_users()
        st.success("Access granted. Below are stored user passwords.")
        st.dataframe(df[['username', 'password_hash']].rename(columns={"password_hash": "password"}))
    else:
        st.info("🔒 Access locked. Enter correct admin key to continue.")


import plotly.express as px

def render_system_settings_page(db):
    st.header("🔧 System Settings")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Reset Parking Spots"):
            db.initialize_parking_spots()
            st.success("Parking spots have been reset.")
            st.rerun()

    with col2:
        if st.button("🧹 Clear Reservation History"):
            empty_df = pd.DataFrame(columns=[
                'id', 'spot_id', 'plate_number', 'customer_name', 'customer_email',
                'customer_phone', 'start_time', 'end_time', 'duration_minutes',
                'status', 'created_at'
            ])
            empty_df.to_csv(db.reservations_file, index=False)
            st.success("Reservation history cleared.")
            st.rerun()

    # 🔄 Live data for chart
    spots_df = db.get_parking_spots()
    status_counts = spots_df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']

    fig = px.pie(status_counts, values='count', names='status', title="Current Spot Status Distribution")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.subheader("📈 Reservation Time Distribution")

    history_df = db.get_reservations_history()

    if not history_df.empty:
        # Ensure datetime format
        history_df['start_time'] = pd.to_datetime(history_df['start_time'])
        history_df['end_time'] = pd.to_datetime(history_df['end_time'])

        fig2 = px.scatter(
            history_df,
            x="start_time",
            y="duration_minutes",
            color="status",
            hover_data=["plate_number", "spot_id"],
            title="Reservation Durations Over Time"
        )
        fig2.update_layout(xaxis_title="Start Time", yaxis_title="Duration (minutes)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No reservation data available yet.")


def render_admin_spot_map(spots_df, db):
    st.header("🗺️ Live Spot Map – Admin Control")

    zones = sorted(spots_df['zone'].unique())
    for zone in zones:
        st.subheader(f"Zone {zone}")
        zone_spots = spots_df[spots_df['zone'] == zone]

        for _, spot in zone_spots.iterrows():
            # Safely get status and emoji
            spot_status = str(spot['status']).strip().lower()
            status_icon = {
                "available": "🟢",
                "reserved": "🟡",
                "occupied": "🔴",
                "maintenance": "🔴"
            }.get(spot_status, "❓")

            with st.expander(f"{status_icon} {spot['spot_id']} – {spot_status.capitalize()}"):
                new_status = st.selectbox(
                    "Status",
                    ["available", "reserved", "occupied", "maintenance"],
                    index=["available", "reserved", "occupied", "maintenance"].index(spot_status),
                    key=f"status_{spot['spot_id']}"
                )
                new_plate = st.text_input("Plate Number", value=spot['plate_number'], key=f"plate_{spot['spot_id']}")
                reserved_by = st.text_input("Reserved By", value=spot['reserved_by'], key=f"by_{spot['spot_id']}")
                reserved_until = st.text_input("Reserved Until", value=spot['reserved_until'], key=f"until_{spot['spot_id']}")

                if st.button(f"✅ Apply to {spot['spot_id']}", key=f"btn_{spot['spot_id']}"):
                    db.update_spot_status(
                        spot_id=spot['spot_id'],
                        status=new_status,
                        plate_number=new_plate,
                        reserved_by=reserved_by,
                        reserved_until=reserved_until
                    )
                    st.success(f"🔄 {spot['spot_id']} updated to '{new_status}'")
                    st.rerun()  # UI + map refresh

    st.markdown("---")
    st.subheader("📊 Spot Map Chart")

    # Reload after updates
    spots_df = db.get_parking_spots()

    spots_df['x'] = spots_df['spot_id'].str.extract('(\d+)').astype(int)
    spots_df['y'] = spots_df['zone'].map({'A': 4, 'B': 3, 'S': 2, 'E': 1})

    # Make sure all statuses appear (even if count = 0)
    for status in ["available", "reserved", "occupied", "maintenance"]:
        if status not in spots_df['status'].unique():
            dummy_row = {
                'spot_id': f'DUMMY_{status}',
                'zone': 'Z',
                'status': status,
                'plate_number': '',
                'reserved_by': '',
                'reserved_until': '',
                'last_updated': '',
                'x': -1,  # hidden from view
                'y': -1
            }
            spots_df = pd.concat([spots_df, pd.DataFrame([dummy_row])], ignore_index=True)

    color_map = {
        "available": "green",
        "reserved": "orange",
        "occupied": "red",
        "maintenance": "gray"
    }

    fig = px.scatter(
        spots_df,
        x='x',
        y='y',
        text='spot_id',
        color='status',
        color_discrete_map=color_map,
        size=[20] * len(spots_df),  # 🔍 Force all dots to be the same size
        size_max=20,  # 📏 Control size scaling
        height=400
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        showlegend=True,
        yaxis_title="Zone",
        xaxis_title="Spot #",
        legend_title="Status"
    )
    st.plotly_chart(fig, use_container_width=True)










__all__ = ["render_admin_spot_map"]
