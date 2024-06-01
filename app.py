import streamlit as st
import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# import matplotlib.pyplot as plt
import plotly.express as px
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
from bson import ObjectId
load_dotenv()

mongodb_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongodb_uri, tlsCAFile=certifi.where())
db = client["khunti"]

col= db["grievance"]

st.set_page_config(layout="wide",page_title="Dashboard")
with open('style.css') as f:
   st.markdown(f"<style>{f.read()}</style>",unsafe_allow_html=True)


# Define a function to create a simple chart for demonstration
def show_admin_page():
    st.title("District Page")
    grievances=list(col.find({}))
    modified_grievances = []
    for grievance in grievances:
     body = grievance['body'].copy()  
     body['_id'] = grievance['_id']
     body['timestamp'] = grievance['timestamp']
     if grievance['state']==1:
         body['status']= "Pending"
     elif grievance['state']==2:
         body['status']= "Completed"
     elif grievance['state']==3:
         body['status']= "Reject"
     if grievance["state"] >0:
         modified_grievances.append(body)
    df=pd.DataFrame(modified_grievances)
    df.columns = df.columns.str.title()
    st.sidebar.image("https://cdn.s3waas.gov.in/s301f78be6f7cad02658508fe4616098a9/uploads/2021/01/2021011537.jpg")
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
            if st.sidebar.button('Login',use_container_width=True):
                st.session_state['logged_in'] = True
                st.experimental_rerun()
    else:
            if st.sidebar.button('Logout',use_container_width=True):
                st.session_state['logged_in'] = False
                st.experimental_rerun()
    # switcher or filter
    st.sidebar.header("Please select filter")
    block=st.sidebar.multiselect("Select Block",options=df["Block"].unique())
    if not block:
        df1=df.copy()
    else:
        df1=df[df['Block'].isin(block)]
    status= st.sidebar.multiselect("Select Status",options=df1["Status"].unique())
    if not status:
        df2=df1.copy()
    else:
        df2=df1[df1['Status'].isin(status)]
    st.dataframe(df2,use_container_width=True)

    id_for_update=st.text_input("Enter ID for update",placeholder="661d04...")
    status_to_update=st.selectbox("Select Status to Update",("Completed","Reject","Pending"))
    if st.button("Update Status"):
        try:
        #  print(id_for_update,status_to_update)
         if status_to_update=="Completed":
             col.update_one({"_id": ObjectId(id_for_update)}, {"$set": { "state": 2}})
             st.experimental_rerun()
         elif status_to_update=="Pending":
             col.update_one({"_id": ObjectId(id_for_update)}, {"$set": { "state": 1}})
             st.experimental_rerun()

         elif status_to_update=="Reject":
             col.update_one({"_id": ObjectId(id_for_update)}, {"$set": { "state": 3}})
             st.experimental_rerun()
      
         st.success("Status updated successfully!")
         st.experimental_rerun()
        except Exception as e:
          st.error(f"An error occurred: {e}")
    
    
    status_counts = df2['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Number of Grievance']
    
   # Plot the bar chart
    st.subheader("Status of the grievances")
    fig = px.bar(status_counts, x="Status", y="Number of Grievance", text=status_counts['Number of Grievance'],
             template="seaborn",color='Status')
    
    

    # Render the chart
    st.plotly_chart(fig, use_container_width=True)

    # bar chart for Grievance for every day
    df2['Timestamp'] = pd.to_datetime(df2['Timestamp'], unit='s')
    df2_grouped = df2.groupby([df2['Timestamp'].dt.strftime('%Y-%m-%d'), 'Status']).size().reset_index(name='count')
    df2_grouped = df2_grouped.sort_values(by='Timestamp')
    

    # Pivot the DataFrame to get dates as index, status as columns, and counts as values
    pivot_df = df2_grouped.pivot(index='Timestamp', columns='Status', values='count').reset_index()
    pivot_df = pivot_df.fillna(0)
    status_values = pivot_df.columns[1:]
    
    fig = px.bar(pivot_df, x='Timestamp', y=status_values, 
             barmode='group', title='Grievances Count by Status Over Time')
    # Render the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
   
    blocks =df["Block"].unique()
    block_status_counts = []

    for block in blocks:
        block_df = df[df['Block'] == block]
        status_counts = block_df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Number of Grievance']
        status_counts['Block'] = block
        block_status_counts.append(status_counts)

    # Concatenate the status counts for each block
    combined_counts = pd.concat(block_status_counts, ignore_index=True)

    # Plot the bar chart
    st.subheader(f"Status of the grievances in blocks")
    fig = px.bar(combined_counts, x="Status", y="Number of Grievance", color='Block',
                barmode='group', text='Number of Grievance', template="seaborn")

    # Render the chart
    st.plotly_chart(fig, use_container_width=True)
    date_filter=st.selectbox("Select a option to filter by timestamp",options=["Week","Month","More than one month"])
    # Filter data based on selected option
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
    if date_filter == "Week":
        # Filter data for the last week
        
        filtered_df = df[df['Timestamp'] >= pd.Timestamp.now() - pd.Timedelta(days=7) ]
        filtered_df=filtered_df[filtered_df['Status'] == 'Pending']
        # print(filtered_df)
    elif date_filter == "Month":
        # Filter data for the last month
        filtered_df = df[df['Timestamp'] >= pd.Timestamp.now() - pd.DateOffset(months=1)]
        filtered_df=filtered_df[filtered_df['Status'] == 'Pending']
    else:
        # Filter data for more than one month
        filtered_df = df[df['Timestamp'] < pd.Timestamp.now() - pd.DateOffset(months=1)]
        filtered_df=filtered_df[filtered_df['Status'] == 'Pending']

    # Group data by Block and Status
    block_status_counts = []
    blocks = filtered_df["Block"].unique()

    for block in blocks:
        block_df = filtered_df[filtered_df['Block'] == block]
        status_counts = block_df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Number of Grievance']
        status_counts['Block'] = block
        block_status_counts.append(status_counts)

    # Check if there are objects to concatenate
    if block_status_counts:
        # Concatenate the status counts for each block
        combined_counts = pd.concat(block_status_counts, ignore_index=True)
        # combined_counts = combined_counts[combined_counts['Status'] == 'Pending']

        # Plot the bar chart
        st.subheader(f"Pending grievances based on selected time filter")
        fig = px.bar(combined_counts, x="Status", y="Number of Grievance", color='Block',
                    barmode='group', text='Number of Grievance', template="seaborn")

        # Render the chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data available for the selected time filter and blocks.")

# Define a function to show the user page with charts


def show_user_page():
    st.title("Block Page")
    st.sidebar.image("https://cdn.s3waas.gov.in/s301f78be6f7cad02658508fe4616098a9/uploads/2021/01/2021011537.jpg")
   
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
                        if st.sidebar.button('Login',use_container_width=True):
                            st.session_state['logged_in'] = True
                            st.experimental_rerun()
    else:
                        if st.sidebar.button('Logout',use_container_width=True):
                            st.session_state['logged_in'] = False
                            st.experimental_rerun()
    grievances=list(col.find({"body.block":st.session_state["block_name"]}))

    modified_grievances = []
    if len(grievances)>0 :
            for grievance in grievances:
                body = grievance['body'].copy()  
                body['_id'] = grievance['_id']
                body['timestamp'] = grievance['timestamp']
                if grievance['state']==1:
                    body['status']= "Pending"
                elif grievance['state']==2:
                    body['status']= "Completed"
                elif grievance['state']==3:
                    body['status']= "Reject"
                if grievance["state"] >0:
                    modified_grievances.append(body)
                df=pd.DataFrame(modified_grievances)
                df.columns = df.columns.str.title()
                # st.sidebar.image("https://cdn.s3waas.gov.in/s301f78be6f7cad02658508fe4616098a9/uploads/2021/01/2021011537.jpg")
                # if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
                #         if st.sidebar.button('Login',use_container_width=True):
                #             st.session_state['logged_in'] = True
                # else:
                #         if st.sidebar.button('Logout',use_container_width=True):
                #             st.session_state['logged_in'] = False
                # switcher or filter
                st.sidebar.header("Please select filter")
                # block=st.sidebar.multiselect("Select Block",options=df["Block"].unique())
                # if not block:
                # else:
                #     df1=df[df['Block'].isin(block)]
                df1=df.copy()
                status= st.sidebar.multiselect("Select Status",options=df1["Status"].unique())
                if not status:
                    df2=df1.copy()
                else:
                    df2=df1[df1['Status'].isin(status)]
                st.dataframe(df2,use_container_width=True)

                id_for_update=st.text_input("Enter ID for update",placeholder="661d04...")
                status_to_update=st.selectbox("Select Status to Update",("Completed","Reject","Pending"))
                if st.button("Update Status"):
                    try:
                    #  print(id_for_update,status_to_update)
                     if status_to_update=="Completed":
                        col.update_one({"_id": ObjectId(id_for_update)}, {"$set": { "state": 2}})
                        st.experimental_rerun()
                     elif status_to_update=="Pending":
                        col.update_one({"_id": ObjectId(id_for_update)}, {"$set": { "state": 1}})
                        st.experimental_rerun()

                     elif status_to_update=="Reject":
                        col.update_one({"_id": ObjectId(id_for_update)}, {"$set": { "state": 3}})
                        st.experimental_rerun()
                
                     st.success("Status updated successfully!")
                     st.experimental_rerun()
                    except Exception as e:
                     st.error(f"An error occurred: {e}")
                
                
                status_counts = df2['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Number of Grievance']
                
            # Plot the bar chart
                st.subheader("Status of the grievances")
                fig = px.bar(status_counts, x="Status", y="Number of Grievance", text=status_counts['Number of Grievance'],
                        template="seaborn",color='Status')
                
                

                # Render the chart
                st.plotly_chart(fig, use_container_width=True)

                # bar chart for Grievance for every day
                df2['Timestamp'] = pd.to_datetime(df2['Timestamp'], unit='s')
                df2_grouped = df2.groupby([df2['Timestamp'].dt.strftime('%Y-%m-%d'), 'Status']).size().reset_index(name='count')
                df2_grouped = df2_grouped.sort_values(by='Timestamp')
                

                # Pivot the DataFrame to get dates as index, status as columns, and counts as values
                pivot_df = df2_grouped.pivot(index='Timestamp', columns='Status', values='count').reset_index()
                pivot_df = pivot_df.fillna(0)
                status_values = pivot_df.columns[1:]
                
                fig = px.bar(pivot_df, x='Timestamp', y=status_values, 
                        barmode='group', title='Grievances Count by Status Over Time')
                # Render the chart in Streamlit
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data available for this blocks.")


   
   

# Define a function for user authentication
def authenticate_user(email, password):
    # Placeholder for actual authentication logic
    # Here we use hardcoded credentials for demonstration purposes
    admin_credentials = {'email': 'admin@example.com', 'password': 'admin123'}
    user_credentials = [
    {'email': 'Arki@example.com', 'password': 'Arki123', 'Block': 'Arki'},
    {'email': 'Karra@example.com', 'password': 'Karra123', 'Block': 'Karra'},
    {'email': 'Khunti@example.com', 'password': 'Khunti123', 'Block': 'Khunti'},
    {'email': 'Murhu@example.com', 'password': 'Murhu123', 'Block': 'Murhu'},
    {'email': 'Rania@example.com', 'password': 'Rania123', 'Block': 'Rania'},
    {'email': 'Torpa@example.com', 'password': 'Torpa123', 'Block': 'Torpa'}
     ]
  
    
    if email == admin_credentials['email'] and password == admin_credentials['password']:
        return 'admin'
    
    else:
        for user in user_credentials:
         if email == user['email'] and password == user['password']:
            st.session_state["block_name"]=user["Block"]
            

            return 'user'
        

# Main app
def main():
    # Create navbar
    # create_navbar()

    # Check if user is logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        # User is not logged in, show login form
        st.title("Login")
        col1,col2=st.columns(2)
        with col1:
            st.markdown('<img src="https://cdn.s3waas.gov.in/s301f78be6f7cad02658508fe4616098a9/uploads/2021/01/2021011537.jpg" width="70%">', unsafe_allow_html=True)
        with col2:
            st.text("")
            st.text("")
            st.text("")
            st.text("")
            st.text("")
            st.text("")
            st.text("")
            st.text("")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button('Login',key="Login",use_container_width=True):
             user_type = authenticate_user(email, password)
             
             if user_type == 'admin':
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = 'admin'
                st.experimental_rerun()
             elif user_type == 'user':
                st.session_state['logged_in'] = True
                st.session_state['user_type'] = 'user'
                st.experimental_rerun()
             else:
                st.error("Invalid credentials")
    else:
        # User is logged in, show appropriate page
        if st.session_state['user_type'] == 'admin':
            show_admin_page()
        elif st.session_state['user_type'] == 'user':
            show_user_page()
        else:
            st.title("Home Page")
            st.write("Welcome to the Streamlit Multi-page App!")

# Run the main function
if __name__ == "__main__":
    main()
