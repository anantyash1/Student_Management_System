import os
import io
from PIL import Image
import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
import re
import bcrypt
import datetime
import pandas as pd
import pywhatkit as pwk
import base64

st.set_page_config(layout = 'wide')

client = MongoClient("mongodb://localhost:27017/")
db = client["anantnew"]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def get_user(username):
    return db.users.find_one({"username": username})

# Authentication and Registration
def register():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["teacher", "student"])
    
    if st.button("Register"):
        if db.users.find_one({"username": username}):
            st.error("Username already exists")
        else:
            hashed_password = hash_password(password)
            db.users.insert_one({"username": username, "password": hashed_password, "role": role})
            st.success("Registered successfully")
            st.experimental_rerun()  # Redirect to main menu


def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        user = get_user(username)
        if user and check_password(password, user["password"]):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.success("Logged in successfully")
            st.experimental_rerun()  # Redirect to main menu
        else:
            st.error("Invalid credentials")





# Role-Based Dashboard
PHOTO_DIR = "uploaded_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)




def teacher_dashboard():
    st.title("Teacher Dashboard")
    

    # def calculate_sgpa(grades):
    # # Example SGPA calculation; modify as needed
    #     if not grades:
    #         return 0
    #     total_marks = sum(grades.values())
    #     num_subjects = len(grades)
    #     return total_marks / num_subjects if num_subjects > 0 else 0

    def assign_ranks(semester):
        # Example rank assignment; modify as needed
        results = list(db.results.find({"semester": semester}))
        if not results:
            return
        # Sort results by SGPA in descending order
        sorted_results = sorted(results, key=lambda x: x['grades'].get('sgpa', 0), reverse=True)
        for rank, result in enumerate(sorted_results, start=1):
            db.results.update_one(
                {"usn": result["usn"], "semester": semester},
                {"$set": {"grades.rank": rank}}
            )
    
    def calculate_sgpa(grades):
        total_marks = sum(grades.values())
        num_subjects = len(grades)
        sgpa = total_marks / num_subjects / 10  # Example calculation
        return round(sgpa, 2)

    # def assign_ranks(results):
    #     results = sorted(results, key=lambda x: x.get('sgpa', 0), reverse=True)
    #     for rank, result in enumerate(results, start=1):
    #         db.results.update_one({"_id": result["_id"]}, {"$set": {"rank": rank}})
    
    # def assign_ranks(results):
    #     results = sorted(results, key=lambda x: x.get('sgpa', 0) if isinstance(x, dict) else 0, reverse=True)
    #     for rank, result in enumerate(results, start=1):
    #         if isinstance(result, dict):
    #             db.results.update_one({"_id": result["_id"]}, {"$set": {"rank": rank}})

        
    def save_photo_to_local(photo, usn):
        """Save photo to the local directory with the USN as the filename in JPG format."""
        try:
            photo_bytes = photo.read()
            image = Image.open(io.BytesIO(photo_bytes))
            resized_image = image.resize((300, 300))  # Adjust size as per your requirement
            resized_image_bytes = io.BytesIO()
            resized_image.save(resized_image_bytes, format='PNG')
            photo_bytes = resized_image_bytes.getvalue()
            file_path = os.path.join(PHOTO_DIR, f"{usn}.jpg")
            
            # Convert image to RGB if necessary and save as JPEG
            if image.mode in ["RGBA", "P"]:
                image = image.convert("RGB")
            
            image.save(file_path, format="JPEG")
            return file_path
        except Exception as e:
            st.error(f"Error saving photo: {e}")
            return None

    def is_valid_usn(usn):
        """Check if the USN is valid (exactly 10 alphanumeric characters)."""
        return len(usn) == 10 and usn.isalnum()

    def is_valid_mobile(mobile):
        """Check if the mobile number starts with a country code and is 10 digits long."""
        return bool(re.match(r'^\+\d{1,4}\d{10}$', mobile))

    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.experimental_rerun()  # Redirect to login page
     
    
    st.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        background-color: #f0f0f0; /* Background color of sidebar */
        padding: 20px; /* Padding around the sidebar content */
    }
    .sidebar .sidebar-content .sidebar-item {
        margin-bottom: 15px; /* Increased space between menu items */
    
         padding: 10px; /* Padding inside each menu item */
        border-radius: 5px; /* Rounded corners for each menu item */
        transition: background-color 0.3s ease; /* Smooth transition for hover effect */
    }
    .sidebar .sidebar-content .sidebar-item:hover {
        background-color: #d3d3d3; /* Hover background color */
        cursor: pointer; /* Pointer cursor on hover */
    }
    .sidebar .sidebar-content .sidebar-item.selected {
        background-color: #a0a0a0; /* Background color when item is selected */
    }

    /* Custom colors for each menu item */
    .sidebar .sidebar-content .sidebar-item:nth-child(1) {
        background-color: #FFD700; /* Gold */
    }
    .sidebar .sidebar-content .sidebar-item:nth-child(2) {
        background-color: #87CEEB; /* Sky Blue */
    }
    .sidebar .sidebar-content .sidebar-item:nth-child(3) {
        background-color: #FFA07A; /* Light Salmon */
    }
    .sidebar .sidebar-content .sidebar-item:nth-child(4) {
        background-color: #98FB98; /* Pale Green */
    }
    .sidebar .sidebar-content .sidebar-item:nth-child(5) {
        background-color: #FFB6C1; /* Light Pink */
    }
    </style>
    """,
    unsafe_allow_html=True
)

    # Sidebar title
    st.sidebar.title("Menu")

# Menu options
    menu_options = ["Manage Students","Manage Assignments","Reports", "Manage Grades", "Track Attendance", "Announcements","Send Message","Assignment Questions"]

# Display menu vertically
    menu = st.sidebar.radio("Select an option", menu_options)

     # Content based on menu selection
    if menu == "Manage Students":
        st.subheader("Manage Students")
        action = st.selectbox("Action", ["Add", "Delete", "View All"])
        
        if action == "Add":
            with st.form("add_student"):
                usn = st.text_input("USN", max_chars=10, help="USN must be exactly 10 alphanumeric characters.")
                name = st.text_input("Name")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                address = st.text_area("Address")
                mobile = st.text_input("Mobile", help="Enter the number with country code.")
                branch = st.text_input("Branch")
                
                # Using st.number_input to ensure numeric input
                current_sem = st.number_input("Current Sem", min_value=1, step=1, format="%d", help="Enter the current semester number.")
                academic_year = st.text_input("Academic Year")
                T_percentage = st.number_input("12th Percentage", min_value=0.0, max_value=100.0, format="%.2f", help="Enter 12th grade percentage.")
                Tenth_percentage = st.number_input("10th Percentage", min_value=0.0, max_value=100.0, format="%.2f", help="Enter 10th grade percentage.")
                
                photo = st.file_uploader("Upload Photo", type=["jpg", "jpeg", "png"])
                
                submit_button = st.form_submit_button("Add Student")
                
                # Validate form fields
                if submit_button:
                    if not all([usn, name, gender, address, mobile, branch, academic_year, T_percentage, Tenth_percentage]):
                        st.error("All fields must be filled.")
                    elif not is_valid_usn(usn):
                        st.error("USN must be exactly 10 alphanumeric characters.")
                    elif db.students.find_one({"usn": usn}):
                        st.error("This USN is already taken.")
                    elif not is_valid_mobile(mobile):
                        st.error("Mobile number must start with country code and be 10 digits long.")
                    elif photo:
                        file_path = save_photo_to_local(photo, usn)
                        if file_path:
                            st.write(f"Photo saved locally at {file_path}")
                            photo.seek(0)  # Reset file pointer to start
                            photo_bytes = photo.read()
                            db.students.insert_one({
                                "usn": usn,
                                "name": name,
                                "gender": gender,
                                "address": address,
                                "mobile": mobile,
                                "branch": branch,
                                "current_sem": current_sem,
                                "academic_year": academic_year,
                                "12_percentage": T_percentage,
                                "10_percentage": Tenth_percentage,
                                "photo": photo_bytes
                            })
                            st.success("Student added successfully")
                        else:
                            st.error("Failed to save photo locally")
                    else:
                        st.error("Please upload a photo")


        elif action == "Delete":
            students = db.students.find()
            student_list = [f"{student['name']} ({student['usn']})" for student in students]
            selected_student = st.selectbox("Select Student", student_list)
            usn = selected_student.split(" ")[-1][1:-1]
            
            if st.button("Delete Student"):
                db.students.delete_one({"usn": usn})
                st.success(f"Student {usn} deleted successfully")

        elif action == "View All":
            students = db.students.find()
            for student in students:
                st.subheader(f"Student: {student['name']}")
                st.write(f"USN: {student['usn']}")
                st.write(f"Gender: {student['gender']}")
                st.write(f"Address: {student['address']}")
                st.write(f"Mobile: {student['mobile']}")
                st.write(f"Branch: {student['branch']}")
                st.write(f"Current Sem: {student['current_sem']}")
                st.write(f"Academic Year: {student['academic_year']}")
                st.write(f"12th Percentage: {student['12_percentage']}%")
                st.write(f"10th Percentage: {student['10_percentage']}%")
                if 'photo' in student:
                    st.image(student['photo'], caption=student['name'], use_column_width=True)
    

    elif menu == "Manage Assignments":
        st.subheader("Manage Assignments")

        if st.session_state.role != 'teacher':
            st.error("You must be a teacher to manage assignments.")
            return

        action = st.selectbox("Action", ["Add", "Edit", "Delete", "View All"])
        
        if action in ["Add", "Edit", "Delete"]:
            students = db.students.find()
            student_list = [f"{student['name']} ({student['usn']})" for student in students]
            selected_student = st.selectbox("Select Student", student_list)
            usn = selected_student.split(" ")[-1][1:-1]

            if action == "Add":
                with st.form("add_assignment"):
                    st.subheader(f"Add Assignments for Student: {usn}")
                    assignment = st.selectbox("Assignment", ["Assignment 1", "Assignment 2", "Assignment 3"])
                    dbms = st.number_input(f"DBMS ({assignment})", min_value=0, max_value=50, step=1, format="%d")
                    daa = st.number_input(f"DAA ({assignment})", min_value=0, max_value=50, step=1, format="%d")
                    microcontroller = st.number_input(f"Microcontroller ({assignment})", min_value=0, max_value=50, step=1, format="%d")
                    maths = st.number_input(f"Maths ({assignment})", min_value=0, max_value=50, step=1, format="%d")
                    uhv = st.number_input(f"UHV ({assignment})", min_value=0, max_value=50, step=1, format="%d")
                    biology = st.number_input(f"Biology ({assignment})", min_value=0, max_value=50, step=1, format="%d")

                    submit_button = st.form_submit_button("Save Assignment")

                    if submit_button:
                        db.assignment.update_one(
                            {"usn": usn, "assignment": assignment},
                            {"$set": {
                                "dbms": dbms,
                                "daa": daa,
                                "microcontroller": microcontroller,
                                "maths": maths,
                                "uhv": uhv,
                                "biology": biology
                            }},
                            upsert=True
                        )
                        st.success(f"{assignment} marks added successfully")
                        # Recalculate and update average marks
                        calculate_and_store_averages()

            elif action == "Edit":
                assignments = db.assignment.find({"usn": usn})
                assignment_list = [assignment["assignment"] for assignment in assignments]
                selected_assignment = st.selectbox("Select Assignment", assignment_list)

                assignment_data = db.assignment.find_one({"usn": usn, "assignment": selected_assignment})

                if assignment_data:
                    with st.form("edit_assignment"):
                        st.subheader(f"Edit {selected_assignment} for Student: {usn}")
                        dbms = st.number_input(f"DBMS ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("dbms", 0))
                        daa = st.number_input(f"DAA ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("daa", 0))
                        microcontroller = st.number_input(f"Microcontroller ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("microcontroller", 0))
                        maths = st.number_input(f"Maths ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("maths", 0))
                        uhv = st.number_input(f"UHV ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("uhv", 0))
                        biology = st.number_input(f"Biology ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("biology", 0))

                        submit_button = st.form_submit_button("Update Assignment")

                        if submit_button:
                            db.assignment.update_one(
                                {"usn": usn, "assignment": selected_assignment},
                                {"$set": {
                                    "dbms": dbms,
                                    "daa": daa,
                                    "microcontroller": microcontroller,
                                    "maths": maths,
                                    "uhv": uhv,
                                    "biology": biology
                                }}
                            )
                            st.success(f"{selected_assignment} marks updated successfully")
                            # Recalculate and update average marks
                            calculate_and_store_averages()

            elif action == "Delete":
                assignments = db.assignment.find({"usn": usn})
                assignment_list = [assignment["assignment"] for assignment in assignments]
                selected_assignment = st.selectbox("Select Assignment", assignment_list)

                if st.button("Delete Assignment"):
                    db.assignment.delete_one({"usn": usn, "assignment": selected_assignment})
                    st.success(f"{selected_assignment} marks deleted successfully")
                    # Recalculate and update average marks
                    calculate_and_store_averages()

        elif action == "View All":
            students = list(db.students.find())
            assignments = ["Assignment 1", "Assignment 2", "Assignment 3"]
            subjects = ["dbms", "daa", "microcontroller", "maths", "uhv", "biology"]

            # Define a function to fetch assignment marks for all students
            def fetch_assignment_marks(assignment):
                data = {"USN": [], "Name": []}
                for subject in subjects:
                    data[subject] = []

                for student in students:
                    usn = student['usn']
                    name = student['name']
                    data["USN"].append(usn)
                    data["Name"].append(name)

                    assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
                    if assignment_data:
                        for subject in subjects:
                            data[subject].append(assignment_data.get(subject, 0))
                    else:
                        for subject in subjects:
                            data[subject].append(0)
                return data

            for assignment in assignments:
                st.subheader(f"{assignment} Marks")
                data = fetch_assignment_marks(assignment)
                df = pd.DataFrame(data)
                st.table(df)

            # Calculate and display the average of the best two assignments
            st.subheader("Average of Best Two Assignments Marks")
            data = {"USN": [], "Name": []}
            for subject in subjects:
                data[subject] = []

            for student in students:
                usn = student['usn']
                name = student['name']
                data["USN"].append(usn)
                data["Name"].append(name)

                best_two_averages = {}
                for subject in subjects:
                    marks = []
                    for assignment in assignments:
                        assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
                        if assignment_data:
                            marks.append(assignment_data.get(subject, 0))
                    best_two_averages[subject] = sum(sorted(marks, reverse=True)[:2]) / 2

                for subject in subjects:
                    data[subject].append(best_two_averages.get(subject, 0))

            df = pd.DataFrame(data)
            st.table(df)
            
            # Store the calculated averages in the database
            for student in students:
                usn = student['usn']
                averages = {}
                for subject in subjects:
                    marks = []
                    for assignment in assignments:
                        assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
                        if assignment_data:
                            marks.append(assignment_data.get(subject, 0))
                    averages[subject] = sum(sorted(marks, reverse=True)[:2]) / 2

                db.average_marks.update_one(
                    {"usn": usn},
                    {"$set": averages},
                    upsert=True
                )

        # if action in ["Add", "Edit", "Delete"]:
        #     students = db.students.find()
        #     student_list = [f"{student['name']} ({student['usn']})" for student in students]
        #     selected_student = st.selectbox("Select Student", student_list)
        #     usn = selected_student.split(" ")[-1][1:-1]

        #     if action == "Add":
        #         with st.form("add_assignment"):
        #             st.subheader(f"Add Assignments for Student: {usn}")
        #             assignment = st.selectbox("Assignment", ["Assignment 1", "Assignment 2", "Assignment 3"])
        #             dbms = st.number_input(f"DBMS ({assignment})", min_value=0, max_value=50, step=1, format="%d")
        #             daa = st.number_input(f"DAA ({assignment})", min_value=0, max_value=50, step=1, format="%d")
        #             microcontroller = st.number_input(f"Microcontroller ({assignment})", min_value=0, max_value=50, step=1, format="%d")
        #             maths = st.number_input(f"Maths ({assignment})", min_value=0, max_value=50, step=1, format="%d")
        #             uhv = st.number_input(f"UHV ({assignment})", min_value=0, max_value=50, step=1, format="%d")
        #             biology = st.number_input(f"Biology ({assignment})", min_value=0, max_value=50, step=1, format="%d")

        #             submit_button = st.form_submit_button("Save Assignment")

        #             if submit_button:
        #                 db.assignment.update_one(
        #                     {"usn": usn, "assignment": assignment},
        #                     {"$set": {
        #                         "dbms": dbms,
        #                         "daa": daa,
        #                         "microcontroller": microcontroller,
        #                         "maths": maths,
        #                         "uhv": uhv,
        #                         "biology": biology
        #                     }},
        #                     upsert=True
        #                 )
        #                 st.success(f"{assignment} marks added successfully")

        #     elif action == "Edit":
        #         assignments = db.assignment.find({"usn": usn})
        #         assignment_list = [assignment["assignment"] for assignment in assignments]
        #         selected_assignment = st.selectbox("Select Assignment", assignment_list)

        #         assignment_data = db.assignment.find_one({"usn": usn, "assignment": selected_assignment})

        #         if assignment_data:
        #             with st.form("edit_assignment"):
        #                 st.subheader(f"Edit {selected_assignment} for Student: {usn}")
        #                 dbms = st.number_input(f"DBMS ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("dbms", 0))
        #                 daa = st.number_input(f"DAA ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("daa", 0))
        #                 microcontroller = st.number_input(f"Microcontroller ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("microcontroller", 0))
        #                 maths = st.number_input(f"Maths ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("maths", 0))
        #                 uhv = st.number_input(f"UHV ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("uhv", 0))
        #                 biology = st.number_input(f"Biology ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("biology", 0))

        #                 submit_button = st.form_submit_button("Update Assignment")

        #                 if submit_button:
        #                     db.assignment.update_one(
        #                         {"usn": usn, "assignment": selected_assignment},
        #                         {"$set": {
        #                             "dbms": dbms,
        #                             "daa": daa,
        #                             "microcontroller": microcontroller,
        #                             "maths": maths,
        #                             "uhv": uhv,
        #                             "biology": biology
        #                         }}
        #                     )
        #                     st.success(f"{selected_assignment} marks updated successfully")

        #     elif action == "Delete":
        #         assignments = db.assignment.find({"usn": usn})
        #         assignment_list = [assignment["assignment"] for assignment in assignments]
        #         selected_assignment = st.selectbox("Select Assignment", assignment_list)

        #         if st.button("Delete Assignment"):
        #             db.assignment.delete_one({"usn": usn, "assignment": selected_assignment})
        #             st.success(f"{selected_assignment} marks deleted successfully")
                    
                    
            

            # elif action == "View All":
            #     students = list(db.students.find())
            #     assignments = ["Assignment 1", "Assignment 2", "Assignment 3"]
            #     subjects = ["dbms", "daa", "microcontroller", "maths", "uhv", "biology"]

            #     # Define a function to fetch assignment marks for all students
            #     def fetch_assignment_marks(assignment):
            #         data = {"USN": [], "Name": []}
            #         for subject in subjects:
            #             data[subject] = []

            #         for student in students:
            #             usn = student['usn']
            #             name = student['name']
            #             data["USN"].append(usn)
            #             data["Name"].append(name)

            #             assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
            #             if assignment_data:
            #                 for subject in subjects:
            #                     data[subject].append(assignment_data.get(subject, 0))
            #             else:
            #                 for subject in subjects:
            #                     data[subject].append(0)
            #         return data

            #     for assignment in assignments:
            #         st.subheader(f"{assignment} Marks")
            #         data = fetch_assignment_marks(assignment)
            #         df = pd.DataFrame(data)
            #         st.table(df)

            #     # Calculate and display the average of the best two assignments
            #     st.subheader("Average of Best Two Assignments Marks")
            #     data = {"USN": [], "Name": []}
            #     for subject in subjects:
            #         data[subject] = []

            #     for student in students:
            #         usn = student['usn']
            #         name = student['name']
            #         data["USN"].append(usn)
            #         data["Name"].append(name)

            #         best_two_averages = {}
            #         for subject in subjects:
            #             marks = []
            #             for assignment in assignments:
            #                 assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
            #                 if assignment_data:
            #                     marks.append(assignment_data.get(subject, 0))
            #             best_two_averages[subject] = sum(sorted(marks, reverse=True)[:2]) / 2

            #         for subject in subjects:
            #             data[subject].append(best_two_averages.get(subject, 0))

            #     df = pd.DataFrame(data)
            #     st.table(df)
    
    
    elif menu == "Reports":
        st.subheader("Reports")

        if st.session_state.role != 'teacher':
            st.error("You must be a teacher to view reports.")
            return

        students = list(db.students.find())
        subjects = ["dbms", "daa", "microcontroller", "maths", "uhv", "biology"]
        data = {subject: [] for subject in subjects}

        # Sort students by the last three characters of their USN
        students.sort(key=lambda student: student['usn'][-3:])

        for student in students:
            usn = student['usn']
            name = student['name']

            # Fetch average marks from the 'average_marks' collection
            average_marks_data = db.average_marks.find_one({"usn": usn})
            if average_marks_data:
                best_two_avg = {subject: average_marks_data.get(subject, 0) for subject in subjects}
            else:
                best_two_avg = {subject: 0 for subject in subjects}

            # Calculate attendance percentage for each subject
            attendance_data = db.attendance.find_one({"usn": usn})
            attendance_percentage = {subject: 0 for subject in subjects}

            if attendance_data:
                for subject, data in attendance_data.get("attendance", {}).items():
                    if data["total"] > 0:
                        attendance_percentage[subject] = (data["attended"] / data["total"]) * 100

            for subject in subjects:
                data[subject].append({
                    "usn": usn,
                    "name": name,
                    "average_marks": best_two_avg[subject],
                    "attendance_percentage": attendance_percentage[subject]
                })

        for subject in subjects:
            st.subheader(f"{subject.upper()}")
            df = pd.DataFrame(data[subject])
            df = df.sort_values(by='usn', key=lambda x: x.str[-3:], ascending=True)
            st.dataframe(df[['usn', 'name', 'average_marks', 'attendance_percentage']])

    
    # elif menu == "Reports":
    #     st.subheader("Reports")

    #     if st.session_state.role != 'teacher':
    #         st.error("You must be a teacher to view reports.")
    #         return

    #     students = list(db.students.find())
    #     subjects = ["dbms", "daa", "microcontroller", "maths", "uhv", "biology"]
    #     data = {subject: [] for subject in subjects}

    #     # Sort students by the last three characters of their USN
    #     students.sort(key=lambda student: student['usn'][-3:])

    #     for student in students:
    #         usn = student['usn']
    #         name = student['name']

    #         # Calculate average of best two assignments for each subject
    #         assignments = db.assignment.find({"usn": usn})
    #         best_two_avg = {subject: 0 for subject in subjects}

    #         for subject in subjects:
    #             marks = [assignment[subject] for assignment in assignments if subject in assignment]
    #             marks.sort(reverse=True)
    #             best_two_avg[subject] = sum(marks[:2]) / 2 if marks else 0

    #         # Calculate attendance percentage for each subject
    #         attendance_data = db.attendance.find_one({"usn": usn})
    #         attendance_percentage = {subject: 0 for subject in subjects}

    #         if attendance_data:
    #             for subject, data in attendance_data.get("attendance", {}).items():
    #                 if data["total"] > 0:
    #                     attendance_percentage[subject] = (data["attended"] / data["total"]) * 100

    #         for subject in subjects:
    #             data[subject].append({
    #                 "usn": usn,
    #                 "name": name,
    #                 "average_marks": best_two_avg[subject],
    #                 "attendance_percentage": attendance_percentage[subject]
    #             })

    #     for subject in subjects:
    #         st.subheader(f"{subject.upper()}")
    #         df = pd.DataFrame(data[subject])
    #         df = df.sort_values(by='usn', key=lambda x: x.str[-3:], ascending=True)
    #         st.dataframe(df[['usn', 'name', 'average_marks', 'attendance_percentage']])


       
    
    # elif menu == "Manage Assignments":
    #     st.subheader("Manage Assignments")

    #     if st.session_state.role != 'teacher':
    #         st.error("You must be a teacher to manage assignments.")
    #         return

    #     action = st.selectbox("Action", ["Add", "Edit", "Delete", "View All"])

    #     if action in ["Add", "Edit", "Delete"]:
    #         students = db.students.find()
    #         student_list = [f"{student['name']} ({student['usn']})" for student in students]
    #         selected_student = st.selectbox("Select Student", student_list)
    #         usn = selected_student.split(" ")[-1][1:-1]

    #         if action == "Add":
    #             with st.form("add_assignment"):
    #                 st.subheader(f"Add Assignments for Student: {usn}")
    #                 assignment = st.selectbox("Assignment", ["Assignment 1", "Assignment 2", "Assignment 3"])
    #                 dbms = st.number_input(f"DBMS ({assignment})", min_value=0, max_value=50, step=1, format="%d")
    #                 daa = st.number_input(f"DAA ({assignment})", min_value=0, max_value=50, step=1, format="%d")
    #                 microcontroller = st.number_input(f"Microcontroller ({assignment})", min_value=0, max_value=50, step=1, format="%d")
    #                 maths = st.number_input(f"Maths ({assignment})", min_value=0, max_value=50, step=1, format="%d")
    #                 uhv = st.number_input(f"UHV ({assignment})", min_value=0, max_value=50, step=1, format="%d")
    #                 biology = st.number_input(f"Biology ({assignment})", min_value=0, max_value=50, step=1, format="%d")

    #                 submit_button = st.form_submit_button("Save Assignment")

    #                 if submit_button:
    #                     db.assignment.update_one(
    #                         {"usn": usn, "assignment": assignment},
    #                         {"$set": {
    #                             "dbms": dbms,
    #                             "daa": daa,
    #                             "microcontroller": microcontroller,
    #                             "maths": maths,
    #                             "uhv": uhv,
    #                             "biology": biology
    #                         }},
    #                         upsert=True
    #                     )
    #                     st.success(f"{assignment} marks added successfully")

    #         elif action == "Edit":
    #             assignments = db.assignment.find({"usn": usn})
    #             assignment_list = [assignment["assignment"] for assignment in assignments]
    #             selected_assignment = st.selectbox("Select Assignment", assignment_list)

    #             assignment_data = db.assignment.find_one({"usn": usn, "assignment": selected_assignment})

    #             if assignment_data:
    #                 with st.form("edit_assignment"):
    #                     st.subheader(f"Edit {selected_assignment} for Student: {usn}")
    #                     dbms = st.number_input(f"DBMS ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("dbms", 0))
    #                     daa = st.number_input(f"DAA ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("daa", 0))
    #                     microcontroller = st.number_input(f"Microcontroller ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("microcontroller", 0))
    #                     maths = st.number_input(f"Maths ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("maths", 0))
    #                     uhv = st.number_input(f"UHV ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("uhv", 0))
    #                     biology = st.number_input(f"Biology ({selected_assignment})", min_value=0, max_value=50, step=1, format="%d", value=assignment_data.get("biology", 0))

    #                     submit_button = st.form_submit_button("Update Assignment")

    #                     if submit_button:
    #                         db.assignment.update_one(
    #                             {"usn": usn, "assignment": selected_assignment},
    #                             {"$set": {
    #                                 "dbms": dbms,
    #                                 "daa": daa,
    #                                 "microcontroller": microcontroller,
    #                                 "maths": maths,
    #                                 "uhv": uhv,
    #                                 "biology": biology
    #                             }}
    #                         )
    #                         st.success(f"{selected_assignment} marks updated successfully")

    #         elif action == "Delete":
    #             assignments = db.assignment.find({"usn": usn})
    #             assignment_list = [assignment["assignment"] for assignment in assignments]
    #             selected_assignment = st.selectbox("Select Assignment", assignment_list)

    #             if st.button("Delete Assignment"):
    #                 db.assignment.delete_one({"usn": usn, "assignment": selected_assignment})
    #                 st.success(f"{selected_assignment} marks deleted successfully")

    #         # elif action == "View All":
    #         #     students = list(db.students.find())
    #         #     assignments = ["Assignment 1", "Assignment 2", "Assignment 3"]
    #         #     subjects = ["dbms", "daa", "microcontroller", "maths", "uhv", "biology"]

    #         #     # Define a function to fetch assignment marks for all students
    #         #     def fetch_assignment_marks(assignment):
    #         #         data = {"USN": [], "Name": []}
    #         #         for subject in subjects:
    #         #             data[subject] = []

    #         #         for student in students:
    #         #             usn = student['usn']
    #         #             name = student['name']
    #         #             data["USN"].append(usn)
    #         #             data["Name"].append(name)

    #         #             assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
    #         #             if assignment_data:
    #         #                 for subject in subjects:
    #         #                     data[subject].append(assignment_data.get(subject, 0))
    #         #             else:
    #         #                 for subject in subjects:
    #         #                     data[subject].append(0)
    #         #         return data

    #         #     for assignment in assignments:
    #         #         st.subheader(f"{assignment} Marks")
    #         #         data = fetch_assignment_marks(assignment)
    #         #         df = pd.DataFrame(data)
    #         #         st.table(df)
            
    #         elif action == "View All":
    #             students = db.students.find()
    #             assignments = ["Assignment 1", "Assignment 2", "Assignment 3"]
    #             subjects = ["dbms", "daa", "microcontroller", "maths", "uhv", "biology"]

    #             for assignment in assignments:
    #                 st.subheader(f"{assignment} Marks")
    #                 data = {"USN": [], "Name": []}
    #                 for subject in subjects:
    #                     data[subject] = []

    #                 for student in students:
    #                     usn = student['usn']
    #                     name = student['name']
    #                     data["USN"].append(usn)
    #                     data["Name"].append(name)

    #                     assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
    #                     if assignment_data:
    #                         for subject in subjects:
    #                             data[subject].append(assignment_data.get(subject, 0))
    #                     else:
    #                         for subject in subjects:
    #                             data[subject].append(0)

    #                 df = pd.DataFrame(data)
    #                 st.table(df)
                
                # st.subheader("Average of Best Two Assignments Marks")
                # data = {"USN": [], "Name": []}
                # for subject in subjects:
                #     data[subject] = []

                #     for student in students:
                #         usn = student['usn']
                #         name = student['name']
                #         data["USN"].append(usn)
                #         data["Name"].append(name)

                #         best_two_averages = {}
                #         for subject in subjects:
                #             marks = []
                #             for assignment in assignments:
                #                 assignment_data = db.assignment.find_one({"usn": usn, "assignment": assignment})
                #                 if assignment_data:
                #                     marks.append(assignment_data.get(subject, 0))
                #             best_two_averages[subject] = sum(sorted(marks, reverse=True)[:2]) / 2

                #         for subject in subjects:
                #             data[subject].append(best_two_averages.get(subject, 0))

                #     df = pd.DataFrame(data)
                #     st.table(df)



                # Calculate and display the average of the best two assignments
                


    elif menu == "Manage Grades":
        st.subheader("Manage Grades")

        # Check if user is a teacher
        user = db.users.find_one({"username": st.session_state.username})
        if user and user.get("role") == "teacher":
            action = st.selectbox("Action", ["Add", "Edit", "Delete", "View All"])

            if action == "Add":
                students = db.students.find()
                student_list = [f"{student['name']} ({student['usn']})" for student in students]
                selected_student = st.selectbox("Select Student", student_list)
                usn = selected_student.split(" ")[-1][1:-1]

                if db.students.find_one({"usn": usn}):
                    semesters = {
                        "Semester 1": ["maths", "c", "mechanical", "english", "physics", "waste_management", "maths_lab", "phy_lab"],
                        "Semester 2": ["chemistry", "civil", "maths", "python", "english", "eng_drawing", "eng_draw_lab", "python_lab"],
                        "Semester 3": ["java", "operating_system", "dsa", "maths", "nss", "social_activity", "dsa_lab", "python_lab"],
                        "Semester 4": ["dbms", "daa", "microcontroller", "maths", "biology", "uhv", "daa_lab", "latex_lab"],
                        # Add subjects for other semesters as needed
                    }

                    for semester, subjects in semesters.items():
                        st.subheader(f"{semester} Marks and SGPA")
                        grades = {}
                        for subject in subjects:
                            grade = st.number_input(f"{subject.replace('_', ' ').title()} Grade ({semester})", min_value=0, max_value=100, step=1, format="%d")
                            if grade >= 0:  # Include grades even if 0
                                grades[subject] = grade

                        # Calculate SGPA
                        sgpa = calculate_sgpa(grades)
                        st.write(f"Calculated SGPA: {sgpa}")

                        # Prepare the data to be saved in the database
                        result_data = {
                            "grades": {
                                **grades,  # Spread the grades dictionary
                                "sgpa": sgpa  # Add SGPA
                            }
                        }

                        if st.button(f"Save {semester} Data"):
                            # Insert or update results data
                            db.results.update_one(
                                {"usn": usn, "semester": semester},
                                {"$set": result_data},
                                upsert=True
                            )
                            st.success(f"{semester} data saved successfully")
                            # Update ranks after saving data
                            assign_ranks(semester)
            
            elif action == "Edit":
                students = db.students.find()
                student_list = [f"{student['name']} ({student['usn']})" for student in students]
                selected_student = st.selectbox("Select Student", student_list)
                usn = selected_student.split(" ")[-1][1:-1]

                if db.results.find_one({"usn": usn}):
                    semesters = {
                        "Semester 1": ["maths", "c", "mechanical", "english", "physics", "waste_management", "maths_lab", "phy_lab"],
                        "Semester 2": ["chemistry", "civil", "maths", "python", "english", "eng_drawing", "eng_draw_lab", "python_lab"],
                        "Semester 3": ["java", "operating_system", "dsa", "maths", "nss", "social_activity", "dsa_lab", "python_lab"],
                        "Semester 4": ["dbms", "daa", "microcontroller", "maths", "biology", "uhv", "daa_lab", "latex_lab"],
                        # Add subjects for other semesters
                    }

                    for semester, subjects in semesters.items():
                        st.subheader(f"{semester} Marks and SGPA")
                        result = db.results.find_one({"usn": usn, "semester": semester})
                        if result:
                            grades = result.get("grades", {})
                            sgpa = result.get("sgpa", 0.0)
                            rank = result.get("rank", 1)
                        else:
                            grades = {subject: 0 for subject in subjects}
                            sgpa = 0.0
                            rank = 1

                        for subject in subjects:
                            grades[subject] = st.number_input(f"{subject.replace('_', ' ').title()} ({semester})", min_value=0, max_value=100, step=1, format="%d", value=grades.get(subject, 0))

                        sgpa = calculate_sgpa(grades)
                        st.write(f"Calculated SGPA: {sgpa}")

                        if st.button(f"Update {semester} Grades"):
                            # Update results data
                            db.results.update_one(
                                {"usn": usn, "semester": semester},
                                {"$set": {"grades": grades, "sgpa": sgpa}}
                            )
                            st.success(f"{semester} grades updated successfully")
                            assign_ranks(list(db.results.find({"semester": semester})))

            elif action == "Delete":
                students = db.students.find()
                student_list = [f"{student['name']} ({student['usn']})" for student in students]
                selected_student = st.selectbox("Select Student", student_list)
                usn = selected_student.split(" ")[-1][1:-1]

                if st.button("Delete Grades"):
                    db.results.delete_many({"usn": usn})
                    st.success(f"All grades for student {usn} deleted successfully")

            elif action == "View All":
                semesters = {
                    "Semester 1": ["maths", "c", "mechanical", "english", "physics", "waste_management", "maths_lab", "phy_lab"],
                    "Semester 2": ["chemistry", "civil", "maths", "python", "english", "eng_drawing", "eng_draw_lab", "python_lab"],
                    "Semester 3": ["java", "operating_system", "dsa", "maths", "nss", "social_activity", "dsa_lab", "python_lab"],
                    "Semester 4": ["dbms", "daa", "microcontroller", "maths", "biology", "uhv", "daa_lab", "latex_lab"],
                    # Add subjects for other semesters
                }
                for semester, subjects in semesters.items():
                    st.subheader(f"{semester} Grades")
                    results = list(db.results.find({"semester": semester}))

                    if results:
                        # Assign ranks based on SGPA
                        assign_ranks(results)

                        # Create a table with students' grades
                        grades_data = []
                        for result in results:
                            usn = result.get("usn", "Unknown USN")
                            student = db.students.find_one({"usn": usn})
                            student_name = student.get("name", "Unknown Name") if student else "Unknown Name"
                            row = {"USN": usn, "Name": student_name}
                            grades = result.get("grades", {})
                            for subject in subjects:
                                row[subject.replace("_", " ").title()] = grades.get(subject, "NA")
                            row["SGPA"] = result.get("sgpa", "NA")
                            row["Rank"] = result.get("rank", "NA")
                            grades_data.append(row)

                        if grades_data:
                            st.table(grades_data)
                        else:
                            st.write(f"No data available for {semester}")
        else:
            st.error("You do not have the required permissions to manage grades.")
    
    
    
  
    
        # Implement grade management functionalities similarly

    
    elif menu == "Track Attendance":
        st.subheader("Track Attendance")

        # Check if user is a teacher
        user = db.users.find_one({"username": st.session_state.username})
        if user and user.get("role") == "teacher":
            action = st.selectbox("Action", ["Add", "Edit", "Delete", "View All", "Shortage of Attendance"])

            semesters = {
                "Semester 1": ["maths", "c", "mechanical", "english", "physics", "waste_management", "maths_lab", "phy_lab"],
                "Semester 2": ["chemistry", "civil", "maths", "python", "english", "eng_drawing", "eng_draw_lab", "python_lab"],
                "Semester 3": ["java", "operating_system", "dsa", "maths", "nss", "social_activity", "dsa_lab", "python_lab"],
                "Semester 4": ["dbms", "daa", "microcontroller", "maths", "biology", "uhv", "daa_lab", "latex_lab"],
                # Add subjects for other semesters
            }

            if action == "Add":
                students = db.students.find()
                student_list = [f"{student['name']} ({student['usn']})" for student in students]
                selected_student = st.selectbox("Select Student", student_list)
                usn = selected_student.split(" ")[-1][1:-1]

                if db.students.find_one({"usn": usn}):
                    for semester, subjects in semesters.items():
                        st.subheader(f"{semester} Attendance")
                        attendance = {}
                        for subject in subjects:
                            attended = st.number_input(f"{subject.replace('_', ' ').title()} ({semester}) - Attended", min_value=0, step=1, format="%d")
                            total = st.number_input(f"{subject.replace('_', ' ').title()} ({semester}) - Total", min_value=0, step=1, format="%d")
                            attendance[subject] = {"attended": attended, "total": total}

                        if st.button(f"Save {semester} Attendance"):
                            # Insert or update attendance data
                            db.attendance.update_one(
                                {"usn": usn, "semester": semester},
                                {"$set": {"subjects": attendance}},
                                upsert=True
                            )
                            st.success(f"{semester} attendance saved successfully")

            elif action == "Edit":
                students = db.students.find()
                student_list = [f"{student['name']} ({student['usn']})" for student in students]
                selected_student = st.selectbox("Select Student", student_list)
                usn = selected_student.split(" ")[-1][1:-1]

                if db.attendance.find_one({"usn": usn}):
                    for semester, subjects in semesters.items():
                        st.subheader(f"{semester} Attendance")
                        result = db.attendance.find_one({"usn": usn, "semester": semester})
                        if result:
                            attendance = result.get("subjects", {})
                        else:
                            attendance = {subject: {"attended": 0, "total": 0} for subject in subjects}

                        for subject in subjects:
                            attended = st.number_input(f"{subject.replace('_', ' ').title()} ({semester}) - Attended", min_value=0, step=1, format="%d", value=attendance.get(subject, {}).get("attended", 0))
                            total = st.number_input(f"{subject.replace('_', ' ').title()} ({semester}) - Total", min_value=0, step=1, format="%d", value=attendance.get(subject, {}).get("total", 0))
                            attendance[subject] = {"attended": attended, "total": total}

                        if st.button(f"Update {semester} Attendance"):
                            # Update attendance data
                            db.attendance.update_one(
                                {"usn": usn, "semester": semester},
                                {"$set": {"subjects": attendance}}
                            )
                            st.success(f"{semester} attendance updated successfully")

            elif action == "Delete":
                students = db.students.find()
                student_list = [f"{student['name']} ({student['usn']})" for student in students]
                selected_student = st.selectbox("Select Student", student_list)
                usn = selected_student.split(" ")[-1][1:-1]

                if st.button("Delete Attendance"):
                    db.attendance.delete_many({"usn": usn})
                    st.success(f"All attendance records for student {usn} deleted successfully")

                        
            elif action == "View All":
                for semester, subjects in semesters.items():
                    st.subheader(f"{semester} Attendance")

                    # Initialize a dictionary to hold attendance data for each student
                    data = {
                        "USN": [],
                        "Name": []
                    }
                    for subject in subjects:
                        data[f"{subject.replace('_', ' ').title()} Attended"] = []
                        data[f"{subject.replace('_', ' ').title()} Total"] = []

                    students = db.students.find()  # Fetch students for each semester loop
                    for student in students:
                        usn = student["usn"]
                        name = student["name"]
                        result = db.attendance.find_one({"usn": usn, "semester": semester})
                        data["USN"].append(usn)
                        data["Name"].append(name)

                        if result:
                            subjects_data = result.get("subjects", {})
                            for subject in subjects:
                                attendance = subjects_data.get(subject, {"attended": 0, "total": 0})
                                data[f"{subject.replace('_', ' ').title()} Attended"].append(attendance.get("attended", 0))
                                data[f"{subject.replace('_', ' ').title()} Total"].append(attendance.get("total", 0))
                        else:
                            for subject in subjects:
                                data[f"{subject.replace('_', ' ').title()} Attended"].append(0)
                                data[f"{subject.replace('_', ' ').title()} Total"].append(0)

                    df = pd.DataFrame(data)
                    st.table(df)


            elif action == "Shortage of Attendance":
                selected_semester = st.selectbox("Select Semester", list(semesters.keys()))
                selected_subject = st.selectbox("Select Subject", semesters[selected_semester])

                if st.button("Show Shortage of Attendance"):
                    data = []
                    students = db.students.find()
                    for student in students:
                        usn = student["usn"]
                        name = student["name"]
                        result = db.attendance.find_one({"usn": usn, "semester": selected_semester})
                        if result:
                            subjects_data = result.get("subjects", {})
                            subject_data = subjects_data.get(selected_subject, {})
                            attended = subject_data.get("attended", 0)
                            total = subject_data.get("total", 0)
                            if total > 0:
                                percentage = (attended / total) * 100
                                if percentage < 85:
                                    data.append({
                                        "USN": usn,
                                        "Name": name,
                                        "Attended": attended,
                                        "Total": total,
                                        "Percentage": round(percentage, 2)
                                    })
                    if data:
                        df = pd.DataFrame(data)
                        st.table(df)
                    else:
                        st.write(f"No students found with less than 85% attendance in {selected_subject} for {selected_semester}.")
        else:
            st.error("You do not have the required permissions to manage attendance.")
            
        # Implement attendance tracking functionalities similarly
        
        
    elif menu == "Announcements":
        st.subheader("Announcements")
        announcement_type = st.radio("Select Announcement Type", ["Text", "Image"])

        if announcement_type == "Text":
            with st.form("announcement_form"):
                text_content = st.text_area("Enter Announcement Text", height=150)
                submit_button = st.form_submit_button("Post Announcement")
                if submit_button:
                    if text_content.strip():
                        announcement = {
                            "type": "text",
                            "content": text_content,
                            "posted_by": st.session_state.username,
                            "timestamp": datetime.datetime.now()
                        }
                        db.announcements.insert_one(announcement)
                        st.success("Announcement posted successfully!")
                    else:
                        st.error("Announcement text cannot be empty.")

        elif announcement_type == "Image":
            with st.form("announcement_form"):
                image_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
                caption = st.text_input("Enter Caption")
                submit_button = st.form_submit_button("Post Announcement")
                if submit_button:
                    if image_file is not None:
                        try:
                            # Save the uploaded image to the 'uploaded_photos' directory
                            os.makedirs('uploaded_photos', exist_ok=True)
                            image_path = os.path.join('uploaded_photos', image_file.name)
                            with open(image_path, 'wb') as f:
                                f.write(image_file.read())

                            # Insert announcement details into the database
                            announcement = {
                                "type": "image",
                                "image_path": image_path,
                                "caption": caption,
                                "posted_by": st.session_state.username,
                                "timestamp": datetime.datetime.now()
                            }
                            db.announcements.insert_one(announcement)
                            st.success("Image announcement posted successfully!")
                        except Exception as e:
                            st.error(f"Error uploading image: {e}")
                    else:
                        st.error("Please upload an image.")

        # Display existing announcements
        st.subheader("Previous Announcements")
        announcements = db.announcements.find().sort("timestamp", -1)
        for announcement in announcements:
            if announcement["type"] == "text":
                st.markdown(f"""
                    <div style="border: 1px solid #13F10C; padding: 10px; margin: 10px 0;">
                        <strong>{announcement['posted_by']}</strong> ({announcement['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})
                        <p>{announcement['content']}</p>
                    </div>
                """, unsafe_allow_html=True)
            elif announcement["type"] == "image":
                image_path = announcement["image_path"]
                if os.path.exists(image_path):
                    st.markdown(f"""
                        <div style="border: 1px solid #13F10C; padding: 10px; margin: 10px 0;">
                            <img src="data:image/jpeg;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" style="width:100%;">
                            <p>{announcement['caption']}</p>
                            <strong>{announcement['posted_by']}</strong> ({announcement['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})
                        </div>
                    """, unsafe_allow_html=True) 
                       

    
    elif menu == "Send Message":
        st.subheader("Send Message")
        with st.form("send_message_form"):
        # Fetch student list for dropdown
           students = db.students.find()
           student_list = [{"name": student["name"], "mobile": student["mobile"]} for student in students]
           student_name_list = [student["name"] for student in student_list]
           selected_student = st.selectbox("Select Student", student_name_list)

        # Fetch selected student's mobile number
           selected_student_mobile = next((student["mobile"] for student in student_list if student["name"] == selected_student), None)
           message = st.text_area("Message", height=150, help="Enter the message to send via WhatsApp.")
           scheduled_time = st.text_input("Scheduled Time (HH:MM)", help="Optional: Schedule the message delivery time (24-hour format). Leave blank for immediate delivery.")
           # Form fields
           
        
        # Validate and send message
           submit_button = st.form_submit_button("Send Message")
           if submit_button:
             if not message.strip():
                st.error("Message cannot be empty.")
             elif not selected_student_mobile:
                st.error("Student mobile number not found.")
             else:
                try:
                    if scheduled_time:
                        scheduled_time = datetime.datetime.strptime(scheduled_time, "%H:%M")
                        pwk.sendwhatmsg(selected_student_mobile, message, scheduled_time.hour, scheduled_time.minute)
                    else:
                        pwk.sendwhatmsg(selected_student_mobile, message)
                    st.success("Message sent successfully!")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
                    
                    
    elif menu == "Assignment Questions":
        st.subheader("Assignment Questions")
        action = st.selectbox("Action", ["Upload", "Delete", "View All"])

        if action == "Upload":
            with st.form("upload_assignment"):
                teacher_name = st.text_input("Teacher Name")
                subject_name = st.text_input("Subject Name")
                semester = st.text_input("Semester")
                assignment_title = st.text_input("Assignment Title")
                assignment_type = st.selectbox("Assignment Type", ["PDF", "Photo"])
                assignment_file = st.file_uploader("Upload Assignment", type=["pdf", "jpg", "jpeg", "png"])

                submit_button = st.form_submit_button("Upload Assignment")

                if submit_button:
                    if not all([teacher_name, subject_name, semester, assignment_title, assignment_type, assignment_file]):
                        st.error("All fields must be filled.")
                    else:
                        assignment_bytes = assignment_file.read()
                        db.assignment_questions.insert_one({
                            "teacher_name": teacher_name,
                            "subject_name": subject_name,
                            "semester": semester,
                            "assignment_title": assignment_title,
                            "assignment_type": assignment_type,
                            "assignment_file": assignment_bytes
                        })
                        st.success("Assignment uploaded successfully")

        elif action == "Delete":
            delete_option = st.radio("Select Option", ["Delete All", "Delete One"])
            
            if delete_option == "Delete All":
                teacher_name = st.text_input("Enter Teacher Name")
                if st.button("Go"):
                    assignments = list(db.assignment_questions.find({"teacher_name": teacher_name}))
                    if not assignments:
                        st.error(f"No assignments found for teacher: {teacher_name}")
                    else:
                        delete_result = db.assignment_questions.delete_many({"teacher_name": teacher_name})
                        if delete_result.deleted_count > 0:
                            st.success(f"All assignments for teacher '{teacher_name}' deleted successfully")
                        else:
                            st.error(f"Failed to delete assignments for teacher '{teacher_name}'")

        elif action == "View All":
            assignments = list(db.assignment_questions.find())
            assignments.reverse()  # Reverse the list to show the latest assignment first
            assignments_count = db.assignment_questions.count_documents({})
            if assignments_count == 0:
                st.info("No assignments found.")
            else:
                st.write("### All Assignments")
                for assignment in assignments:
                    st.write("---")
                    st.write(f"*Teacher Name:* {assignment.get('teacher_name', 'N/A')}")
                    st.write(f"*Subject Name:* {assignment.get('subject_name', 'N/A')}")
                    st.write(f"*Semester:* {assignment.get('semester', 'N/A')}")
                    st.write(f"*Assignment Title:* {assignment.get('assignment_title', 'N/A')}")
                    st.write(f"*Assignment Type:* {assignment.get('assignment_type', 'N/A')}")
                    if assignment.get('assignment_type') == "PDF":
                        st.markdown(get_pdf_viewer_data(assignment.get('assignment_file', b'')), unsafe_allow_html=True)

def get_pdf_viewer_data(pdf_bytes):
    """Display PDF file content in Streamlit."""
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{pdf_base64}" width="700" height="1000" type="application/pdf">'
    return pdf_display

                    



# Add custom CSS for hover effects and tooltips
st.markdown(
"""
<style>
.sidebar .sidebar-content {
    background-color: #f0f0f0; /* Background color of sidebar */
    padding: 20px; /* Padding around the sidebar content */
}
.sidebar .sidebar-content .sidebar-item {
    margin-bottom: 15px; /* Increased space between menu items */
    padding: 10px; /* Padding inside each menu item */
    border-radius: 5px; /* Rounded corners for each menu item */
    transition: background-color 0.3s ease; /* Smooth transition for hover effect */
}
.sidebar .sidebar-content .sidebar-item:hover {
    background-color: #87CEEB; /* Hover background color - change this color as desired */
    cursor: pointer; /* Pointer cursor on hover */
}
.sidebar .sidebar-content .sidebar-item.selected {
    background-color: #a0a0a0; /* Background color when item is selected */
}

/* Custom colors for each menu item */
.sidebar .sidebar-content .sidebar-item:nth-child(1) {
    background-color: #FFD700; /* Gold */
}
.sidebar .sidebar-content .sidebar-item:nth-child(2) {
    background-color: #87CEEB; /* Sky Blue */
}
.sidebar .sidebar-content .sidebar-item:nth-child(3) {
    background-color: #FFA07A; /* Light Salmon */
}
.sidebar .sidebar-content .sidebar-item:nth-child(4) {
    background-color: #98FB98; /* Pale Green */
}
.sidebar .sidebar-content .sidebar-item:nth-child(5) {
    background-color: #FFB6C1; /* Light Pink */
}
</style>
""",
unsafe_allow_html=True)


#student dashboard
def student_dashboard():
    st.title("Student Dashboard")
    if st.button("Logout"):
        st.session_state.logged_in = False

    # Add style to the sidebar menu to display items vertically with some spacing and hover effect
    
    

        

    # Custom CSS for styling the sidebar and radio buttons
    st.markdown("""
        <style>
            .sidebar-content {
                background-color: #f0f0f0; /* Background color of sidebar */
                padding: 25px; /* Padding around the sidebar content */
            }
            .sidebar .sidebar-content .sidebar-item {
                font-size: 35px; /* Larger font size */
                font-weight: bold; /* Bold text */
                margin-bottom: 20px; /* Increased space between menu items */
                padding: 15px; /* Padding inside each menu item */
                border-radius: 10px; /* Rounded corners for each menu item */
                transition: background-color 0.3s ease; /* Smooth transition for hover effect */
                display: flex;
                align-items: center;
                justify-content: center;
                height: calc(100vh / 5); /* Equal height for each item */
            }
            .sidebar .sidebar-content .sidebar-item:hover {
                background-color: #d3d3d3; /* Hover background color */
                cursor: pointer; /* Pointer cursor on hover */
            }
            .sidebar .sidebar-content .sidebar-item.selected {
                background-color: #a0a0a0; /* Background color when item is selected */
            }

            /* Custom colors for each menu item */
            .sidebar .sidebar-content .sidebar-item:nth-child(1) {
                background-color: #FFD700; /* Gold */
            }
            .sidebar .sidebar-content .sidebar-item:nth-child(2) {
                background-color: #87CEEB; /* Sky Blue */
            }
            .sidebar .sidebar-content .sidebar-item:nth-child(3) {
                background-color: #FFA07A; /* Light Salmon */
            }
            .sidebar .sidebar-content .sidebar-item:nth-child(4) {
                background-color: #98FB98; /* Pale Green */
            }
            .sidebar .sidebar-content .sidebar-item:nth-child(5) {
                background-color: #FFB6C1; /* Light Pink */
            }
            .css-1d391kg {
                padding: 0 !important; /* Remove padding to make items fill the sidebar */
            }
            /* Custom styles for the radio buttons and labels */
            .stRadio > div {
                margin-bottom: 20px; /* Space between radio buttons */
            }
            .stRadio > div > label {
                font-size: 20px; /* Larger font size for labels */
                font-weight: bold; /* Bold text for labels */
                padding: 10px 20px; /* Padding around each label */
                border-radius: 5px; /* Rounded corners for each label */
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.3s ease; /* Smooth transition for hover effect */
            }
            .stRadio > div > label:hover {
                background-color: #d3d3d3; /* Hover background color for labels */
                cursor: pointer; /* Pointer cursor on hover */
            }
            .stRadio > div > label[data-selected="true"] {
                background-color: #a0a0a0; /* Background color for selected label */
            }
        </style>
        """, unsafe_allow_html=True)

    # Sidebar title
    st.sidebar.title("Menu")

    # Menu options
    menu_options = ["Profile", "Assignments", "Grades", "Attendance", "Announcements","Assignment Questions","Upload Assignment"]

    # Display menu options with custom styling
    menu_selection = st.sidebar.radio(
        "Select an option",
        menu_options,
        index=0,
        key='sidebar_radio_unique',
    )

    if menu_selection == "Profile":
        st.subheader("Profile")
        
        # Fetch student data from MongoDB based on entered USN
        usn = st.text_input("Enter your USN", max_chars=10, help="Enter your unique USN to fetch your profile.")
        if st.button("Enter"):
            query = {"usn": usn}  # Constructing query dictionary
            cursor = db.students.find(query)  # Querying the collection
            
            # Iterate over cursor to display results
            for student in cursor:
                # Display photo if available
                if 'photo' in student:
                    st.image(student['photo'],  width=150, use_column_width=False)
                
                st.markdown("<hr>", unsafe_allow_html=True)  # Horizontal line separator
                
                st.markdown(f"*Name:* {student['name']}  \n"
                            f"*USN:* {student['usn']}  \n"
                            f"*Gender:* {student['gender']}  \n"
                            f"*Address:* {student['address']}  \n"
                            f"*Mobile:* {student['mobile']}  \n"
                            f"*Branch:* {student['branch']}  \n"
                            f"*Current Sem:* {student['current_sem']}  \n"
                            f"*Academic Year:* {student['academic_year']}  \n"
                            f"*12th Percentage:* {student['12_percentage']}  \n"
                            f"*10th Percentage:* {student['10_percentage']}  \n"
                            , unsafe_allow_html=True)

        
    elif menu_selection == "Assignments":
        st.subheader("Assignments")
        
        usn = st.text_input("Enter USN to View Assignments", max_chars=10, help="Enter your USN to view your assignment marks.")
        
        if st.button("View Assignments"):
            student_assignment = db.assignment.find_one({"usn": usn})
            if student_assignment:
                df = pd.DataFrame([student_assignment])
                df = df.drop(columns=["_id", "usn"])  # Drop unnecessary columns
                st.table(df)
            else:
                st.error(f"No assignments found for USN: {usn}")

        # Implement view and submit assignments functionalities similarly

    elif menu_selection == "Grades":
        st.subheader("Grades")

        usn = st.text_input("Enter USN to View Grades", max_chars=10, help="Enter your USN to view your semester grades.")
        
        if st.button("View Grades"):
            student_grades = db.results.find_one({"usn": usn})

            if student_grades:
                # Iterate over each semester in the student grades
                for semester, grades in student_grades.items():
                    if semester not in ["_id", "usn"]:
                        st.subheader(f"{semester} Grades")

                        # Check if grades is a dictionary
                        if isinstance(grades, dict):
                            # Initialize lists to collect data
                            subjects = []
                            marks = []
                            
                            
                            # Populate the subjects and marks lists
                            for subject, mark in grades.items():
                                if subject not in ["sgpa", "rank"]:
                                    subjects.append(subject.replace('_', ' ').title())
                                    marks.append(mark)

                            # Add SGPA and rank to the lists
                            subjects.append("SGPA")
                            marks.append(grades.get("sgpa", "N/A"))
                            subjects.append("Rank")
                            marks.append(grades.get("rank", "N/A"))

                            # Create and display the DataFrame
                            data = {
                                "Subject": subjects,
                                "Marks": marks
                            }
                            df = pd.DataFrame(data)
                            st.table(df)
                        else:
                            st.error(f"Grades data for {semester} is not in the expected format.")
            else:
                st.error(f"No grades found for USN: {usn}")

    # elif menu_selection == "Grades":
    #     st.subheader("Grades")
        
    #     usn = st.text_input("Enter USN to View Grades", max_chars=10, help="Enter your USN to view your semester grades.")
        
    #     if st.button("View Grades"):
    #         student_grades = db.results.find_one({"usn": usn})
    #         # grades_list = list(grades_cursor)
            
    #         if student_grades:
    #             df = pd.DataFrame(student_grades)
    #             df = df.drop(columns=["_id", "usn"])  # Drop unnecessary columns
    #             st.table(df)
    #         else:
    #             st.error(f"No grades found for USN: {usn}")
        # Implement view grades functionalities similarly

    elif menu_selection == "Attendance":
        st.subheader("Attendance")
        
        usn = st.text_input("Enter USN to View Attendance", max_chars=10, help="Enter your USN to view your attendance records.")
        
        if st.button("View Attendance"):
            attendance_cursor = db.attendance.find({"usn": usn})
            attendance_list = list(attendance_cursor)
            
            if attendance_list:
                df = pd.DataFrame(attendance_list)
                df = df.drop(columns=["_id", "usn"])  # Drop unnecessary columns
                st.table(df)
            else:
                st.error(f"No attendance records found for USN: {usn}")
        # Implement view attendance functionalities similarly

    elif menu_selection == "Announcements":
        st.subheader("Announcements")

        # Display existing announcements
        st.subheader("Previous Announcements")
        announcements = db.announcements.find().sort("timestamp", -1)
        for announcement in announcements:
            if announcement["type"] == "text":
                st.markdown(f"**Posted by: {announcement['posted_by']} ({announcement['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})**")
                st.write(announcement["content"])
            elif announcement["type"] == "image":
                image_path = announcement["image_path"]
                if os.path.exists(image_path):
                    st.image(image_path, caption=announcement["caption"], use_column_width=True)
                    st.write(f"**Posted by: {announcement['posted_by']} ({announcement['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})**")
     
     
    #placed it as the last option inside the student dashoard

    elif menu_selection == "Assignment Questions":
        st.subheader("Assignment Questions")

        teacher_name = st.text_input("Enter Teacher Name")
        subject_name = st.text_input("Enter Subject Name")
        semester = st.text_input("Enter Semester")

        if st.button("Show Assignments"):
            query = {
                "teacher_name": teacher_name,
                "subject_name": subject_name,
                "semester": semester
            }
            assignments = list(db.assignment_questions.find(query))

            if assignments:
                st.write("### Assignments")
                for assignment in assignments:
                    st.write(f"*Assignment Title:* {assignment.get('assignment_title', 'N/A')}")
                    st.write(f"*Assignment Type:* {assignment.get('assignment_type', 'N/A')}")
                    if assignment.get('assignment_type') == "PDF":
                        st.markdown(get_pdf_viewer_data(assignment.get('assignment_file', b'')), unsafe_allow_html=True)
                    st.write("---")
            else:
                st.error("No assignments found for the specified criteria.")
    
    
    #after the upper 

    
    elif menu_selection == "Upload Assignment":
        st.subheader("Upload Assignment")

        # Input fields for assignment details
        student_name = st.text_input("Enter Student Name")
        usn = st.text_input("Enter USN")
        subject_name = st.text_input("Enter Subject Name")
        section = st.text_input("Enter Section")
        branch = st.text_input("Enter Branch")
        uploaded_file = st.file_uploader("Upload Answer (PDF)", type=['pdf'])

        if st.button("Upload"):
            if student_name and usn and subject_name and section and branch and uploaded_file:
                # Store the uploaded file to 'student_answers' collection in 'anantnew' database
                file_details = {
                    "student_name": student_name,
                    "usn": usn,
                    "subject_name": subject_name,
                    "section": section,
                    "branch": branch,
                    "answer_file": uploaded_file.read(),  # Store the file content as bytes
                    "upload_time": datetime.datetime.now()
                }
                db.student_answers.insert_one(file_details)
                st.success("Assignment uploaded successfully!")
            else:
                st.error("Please fill in all the fields and upload a PDF file.")
    

def get_pdf_viewer_data(pdf_bytes):
    """Display PDF file content in Streamlit."""
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{pdf_base64}" width="700" height="1000" type="application/pdf">'
    return pdf_display       
            
        


        # Implement view announcements functionalities similar


# Main App Logic
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if st.session_state.logged_in:
        if st.session_state.role == "teacher":
            teacher_dashboard()
        elif st.session_state.role == "student":
            student_dashboard()
    else:
        page = st.sidebar.selectbox("Page", ["Login", "Register"])
        if page == "Login":
            login()
        elif page == "Register":
            register()