import streamlit as st
from user import render_user_login_page



st.set_page_config(
    page_title="BASE-SmartPark",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from datetime import datetime
from web import (
    ParkingDatabase,
    render_dashboard_page,
    render_reservation_page,
    render_admin_login_page
)
from admin import (
    render_analytics_page,
    render_system_settings_page,
    render_admin_spot_map,
    render_user_admin_panel,
    render_user_passwords_view
)

# Cache database
@st.cache_resource
def get_db():
    return ParkingDatabase()

# Init session state
def init_session():
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'admin_username' not in st.session_state:
        st.session_state.admin_username = ""
    if 'page_refresh' not in st.session_state:
        st.session_state.page_refresh = 0
    if 'user_plate' not in st.session_state:
        st.session_state.user_plate = ""

# Reservation status tracker (User)
def render_reservation_status_page(db):
    st.header("📟 Reservation Status Tracker")
    plate = st.text_input("🔍 Enter your license plate to track reservation")
    if plate:
        st.session_state.user_plate = plate.upper()

    if st.session_state.user_plate:
        df = db.get_reservations_history()
        active = df[(df['plate_number'] == st.session_state.user_plate) & (df['status'] == 'active')]

        if active.empty:
            st.info("No active reservation found for this plate.")
        else:
            res = active.iloc[-1]
            st.success(f"🅿️ Spot: {res['spot_id']} | 👤 Name: {res['customer_name']}")

            end_time = datetime.fromisoformat(res['end_time'])
            remaining = end_time - datetime.now()
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                st.info(f"⏳ Time remaining: {mins} min {secs} sec")
            else:
                st.warning("Reservation has likely expired.")

# Admin Spot Grid View with Manual Override
def render_admin_spot_grid(spots_df, db):
    st.header("🗺️ Live Spot Map - Admin Control")
    zones = spots_df['zone'].unique()
    zone_titles = {"B": "Regular","A": "VIP",  "S": "Staff", "E": "Emergency"}

    for zone in sorted(zones):
        st.subheader(f"Zone {zone} - {zone_titles.get(zone, '')}")
        zone_spots = spots_df[spots_df['zone'] == zone].sort_values('spot_id')
        cols = st.columns(5)
        for idx, (_, spot) in enumerate(zone_spots.iterrows()):
            with cols[idx % 5]:
                color = {
                    'available': '🟢',
                    'reserved': '🟡',
                    'occupied': '🔴',
                    'maintenance': '🔧'
                }.get(spot['status'], '⚪')
                label = f"{color} {spot['spot_id']}"
                st.markdown(label)

                if st.button(f"⚙️ Manage {spot['spot_id']}", key=f"{zone}-{spot['spot_id']}"):
                    with st.form(f"form-{spot['spot_id']}"):
                        new_status = st.selectbox("New Status", ["available", "reserved", "occupied", "maintenance"], index=["available", "reserved", "occupied", "maintenance"].index(spot['status']))
                        new_plate = st.text_input("Plate Number", spot['plate_number'])
                        reserved_by = st.text_input("Reserved By", spot['reserved_by'])
                        reserved_until = st.text_input("Reserved Until", spot['reserved_until'])
                        if st.form_submit_button("✅ Apply Changes"):
                            db.update_spot_status(spot['spot_id'], new_status, new_plate, reserved_by, reserved_until)
                            st.success(f"Updated {spot['spot_id']}")
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


# App entrypoint
def main():
    init_session()
    db = get_db()
    db.clean_expired_reservations()
    spots_df = db.get_parking_spots()
    reservations_df = db.get_reservations_history()


    st.sidebar.title("🧭 SmartPark Navigation")
    pages = ["🏠 Dashboard",
             "🎫 Reservation",
             "📟 Track Status",
             "👤 User Portal",
             "🔐 Admin Login"
             ]
    if st.session_state.admin_logged_in:
        pages += ["📊 Analytics",
                  "🔧 System Settings",
                  "🗺️ Admin Spot Map",
                  "👥 Manage Users",
                  "🔑 View User Passwords"
                  ]

    selection = st.sidebar.radio("Choose a page", pages)

    if selection == "🏠 Dashboard":
        render_dashboard_page(spots_df, reservations_df)

    elif selection == "🎫 Reservation":
        render_reservation_page(spots_df, db)

    elif selection == "📟 Track Status":
        render_reservation_status_page(db)
    elif selection == "📊 Analytics":
        render_analytics_page(spots_df, reservations_df)

    elif selection == "🔧 System Settings":
        render_system_settings_page(db)


    elif selection == "🗺️ Admin Spot Map":
        render_admin_spot_map(spots_df, db)

    elif selection == "🔐 Admin Login":
        render_admin_login_page()

    elif selection == "👤 User Portal":
        render_user_login_page()

    elif selection == "👥 Manage Users":
        if st.session_state.get("admin_logged_in", False):
            render_user_admin_panel()

        else:
            st.warning("Admins only")

    elif selection == "🔑 View User Passwords":
        if st.session_state.get("admin_logged_in", False):
            render_user_passwords_view()
        else:
            st.warning("Admins only.")




if __name__ == "__main__":
    main()
