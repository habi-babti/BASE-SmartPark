import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os
import random
import string

# ==== Database Class ====
class ParkingDatabase:
    def __init__(self, data_dir="parking_data"):
        self.data_dir = data_dir
        self.parking_spots_file = os.path.join(data_dir, "parking_spots.csv")
        self.reservations_file = os.path.join(data_dir, "reservations_history.csv")
        self.emergency_vehicles_file = os.path.join(data_dir, "emergency_vehicles.csv")
        self.admin_users_file = os.path.join(data_dir, "admin_users.csv")
        self.anpr_detections_file = os.path.join(data_dir, "anpr_detections.csv")
        self.init_database()

    def init_database(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.parking_spots_file):
            self.initialize_parking_spots()
        if not os.path.exists(self.reservations_file):
            pd.DataFrame(columns=[
                'id', 'spot_id', 'plate_number', 'customer_name', 'customer_email',
                'customer_phone', 'start_time', 'end_time', 'duration_minutes',
                'status', 'created_at'
            ]).to_csv(self.reservations_file, index=False)
        if not os.path.exists(self.emergency_vehicles_file):
            pd.DataFrame([{ "plate_number": "AMB001", "vehicle_type": "Ambulance",
                "description": "City Hospital", "is_active": True,
                "added_date": datetime.now().isoformat()
            }]).to_csv(self.emergency_vehicles_file, index=False)
        if not os.path.exists(self.admin_users_file):
            hash_ = hashlib.sha256("admin123".encode()).hexdigest()
            pd.DataFrame([{
                "username": "admin", "password_hash": hash_, "email": "admin@smartpark.com",
                "role": "super_admin", "created_at": datetime.now().isoformat(), "last_login": ""
            }]).to_csv(self.admin_users_file, index=False)
        if not os.path.exists(self.anpr_detections_file):
            pd.DataFrame(columns=[
                'id', 'plate_number', 'confidence', 'detection_time',
                'camera_location', 'is_emergency', 'processed'
            ]).to_csv(self.anpr_detections_file, index=False)

    def initialize_parking_spots(self):
        zones = {"A": "VIP", "B": "Regular", "S": "Staff", "E": "Emergency"}
        spots = []
        for zone in zones:
            for i in range(1, 11):
                spot_id = f"{zone}{i:02}"
                spots.append({
                    "spot_id": spot_id, "zone": zone, "status": "available",
                    "plate_number": "", "reserved_by": "", "reserved_until": "",
                    "last_updated": datetime.now().isoformat()
                })
        pd.DataFrame(spots).to_csv(self.parking_spots_file, index=False)

    def get_parking_spots(self):
        return pd.read_csv(self.parking_spots_file)

    def get_reservations_history(self):
        try:
            return pd.read_csv(self.reservations_file)
        except:
            return pd.DataFrame()

    def add_reservation(self, spot_id, plate_number, name, email, phone, duration):
        start = datetime.now()
        end = start + timedelta(minutes=duration)
        df = self.get_reservations_history()
        new_id = len(df) + 1
        new_row = pd.DataFrame([{
            "id": new_id, "spot_id": spot_id, "plate_number": plate_number, "customer_name": name,
            "customer_email": email, "customer_phone": phone,
            "start_time": start.isoformat(), "end_time": end.isoformat(),
            "duration_minutes": duration, "status": "active", "created_at": datetime.now().isoformat()
        }])
        df = pd.concat([df, new_row])
        df.to_csv(self.reservations_file, index=False)

        # Update spot
        self.update_spot_status(spot_id, 'reserved', plate_number, name, end.isoformat())

    def update_spot_status(self, spot_id, status, plate_number='', reserved_by='', reserved_until=''):
        df = pd.read_csv(self.parking_spots_file)
        mask = df['spot_id'] == spot_id
        df.loc[mask, 'status'] = status
        df.loc[mask, 'plate_number'] = plate_number
        df.loc[mask, 'reserved_by'] = reserved_by
        df.loc[mask, 'reserved_until'] = reserved_until
        df.loc[mask, 'last_updated'] = datetime.now().isoformat()
        df.to_csv(self.parking_spots_file, index=False)

    def clean_expired_reservations(self):
        now = datetime.now()
        df = self.get_reservations_history()
        updated = False
        for i, row in df.iterrows():
            if row['status'] == 'active' and datetime.fromisoformat(row['end_time']) < now:
                df.at[i, 'status'] = 'expired'
                self.update_spot_status(
                    spot_id=row['spot_id'],
                    status='available',
                    plate_number='',
                    reserved_by='',
                    reserved_until=''
                )
                updated = True
        if updated:
            df.to_csv(self.reservations_file, index=False)
def update_spot_status(self, spot_id, status, plate_number='', reserved_by='', reserved_until=''):
    df = pd.read_csv(self.parking_spots_file)
    mask = df['spot_id'] == spot_id
    df.loc[mask, 'status'] = status
    df.loc[mask, 'plate_number'] = plate_number
    df.loc[mask, 'reserved_by'] = reserved_by
    df.loc[mask, 'reserved_until'] = reserved_until
    df.loc[mask, 'last_updated'] = datetime.now().isoformat()
    df.to_csv(self.parking_spots_file, index=False)

# ==== UI ====
def render_dashboard_page(spots_df, reservations_df):
    st.header("🏠 SmartPark Dashboard")
    col1, col2 = st.columns(2)
    col1.metric("🅿️ Total Spots", len(spots_df))
    col2.metric("📋 Total Reservations", len(reservations_df))
    st.dataframe(spots_df.head())
def generate_random_plate():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=4))
    return f"{letters}{numbers}"

def render_reservation_page(spots_df, db):
    st.header("🎫 Make a Reservation")
    available = spots_df[spots_df['status'] == 'available']
    if available.empty:
        st.warning("No available spots")
        return
    st.subheader("⚡ Quick Reservation (ANPR Auto Mode)")
    if st.button("🚗 Auto-Assign Spot & Detect Plate"):
        selected_spot = available.iloc[0]['spot_id']
####################################################################################################################################################
        detected_plate = generate_random_plate()  # Replace with actual ANPR logic important #######################################################
####################################################################################################################################################
        db.add_reservation(
            spot_id=selected_spot,
            plate_number=detected_plate,
            name="Auto-ANPR",
            email="auto@smartpark.com",
            phone="0000000000",
            duration=60
        )
        st.success(f"✅ Reserved {selected_spot} for {detected_plate} using ANPR!")
        st.rerun()

    with st.form("reserve"):
        zone = st.selectbox("Zone", available['zone'].unique())
        spot = st.selectbox("Spot", available[available['zone'] == zone]['spot_id'])
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        plate = st.text_input("Plate Number")
        duration = st.selectbox("Duration", [30, 60, 120, 180])
        submit = st.form_submit_button("Reserve")

        if submit:
            db.add_reservation(spot, plate, name, email, phone, duration)
            st.success("Reservation created!")
            st.rerun()




def render_admin_login_page():
    st.header("🔐 Admin Login")
    with st.form("login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            db = ParkingDatabase()
            admin_df = pd.read_csv(db.admin_users_file)
            hashed = hashlib.sha256(pwd.encode()).hexdigest()
            if not admin_df[(admin_df['username'] == user) & (admin_df['password_hash'] == hashed)].empty:
                st.session_state.admin_logged_in = True
                st.session_state.admin_username = user
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Wrong credentials")

def render_tracking_page(db):
    st.header("📍 Track Your Reservation")
    all_plates = db.get_reservations_history()['plate_number'].dropna().unique()
    plate = st.selectbox("🔎 Select or enter your plate:", all_plates)

    if plate and st.button("Check Status"):
        history = db.get_reservations_history()
        result = history[history['plate_number'].str.upper() == plate.upper()]
        if not result.empty:
            latest = result.sort_values("created_at", ascending=False).iloc[0]
            st.success(f"✅ Reservation Found for {plate}")
            st.markdown(f"""
            **Spot ID**: {latest['spot_id']}  
            **Start Time**: {latest['start_time']}  
            **End Time**: {latest['end_time']}  
            **Status**: `{latest['status']}`  
            """)
        else:
            st.error("❌ No reservation found for that plate.")



# --- EXPORTS ---
__all__ = [
    "ParkingDatabase",
    "render_dashboard_page",
    "render_reservation_page",
    "render_admin_login_page",
    "render_tracking_page"
]