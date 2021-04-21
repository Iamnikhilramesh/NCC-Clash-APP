#Required libraries
import streamlit as st
import pandas as pd
import base64
import pickle
#config
st.set_option('deprecation.showPyplotGlobalUse', False)
#Application title and info
st.title("Utilizing Machine Learning to Detect Non-pseudo/pseudo Design Conflicts in BIM Models")
st.write("...")


#definations
#Data prepration function
#Function to clean the data 
def prepare_data(df1,phase):
    try:
        if "Issue Description" in df1:
            df = []
            df = pd.DataFrame(df)
            
            #split the data value columns in issue description
            new = df1["Issue Description"].str.split(":", n = 1, expand = True) 
            df1["required"]= new[1]
    
            #Split the above required column 
            new = df1["required"].str.split(",", n = 5, expand = True) 
            df1["component1"]= new[0] 
            df1["component2"]= new[1]
            df1["x"]= new[2]
            df1["y"]= new[3]
            df1["z"]= new[4]
            df1["volume"]= new[5]
            
            #new dataframe with split values in component1 columns
            new = df1["component1"].str.split(".", n = 1, expand = True) 
            df1['comp1'] = new[0]
            df1['distance1'] = new[1]
            
            #new dataframe with split values in distance columns
            new = df1["distance1"].str.split(".", n = 2, expand = True) 
            df1['distance_1'] = new[0]
            df1['distance1_2'] = new[1]
            df1['distance'] = df1['distance_1'].str.cat(df1['distance1_2'], sep =".") 

            #new dataframe with split values in component2 columns
            new = df1["component2"].str.split(".", n = 1, expand = True) 
            df1['comp2'] = new[0]
            df1['distance2'] = new[1]
            
            #X_axis data extract withour the measure
            new = df1["x"].str.split("m", n = 1, expand = True) 
            df1['x_axis'] = new[0]
            
            #y_axis data extract withour the measure
            new = df1["y"].str.split("m", n = 1, expand = True) 
            df1['y_axis'] = new[0]
            
            #z_axis data extract withour the measure
            new = df1["z"].str.split("m", n = 1, expand = True) 
            df1['z_axis'] = new[0] 
            
            #Volume extract without the measure
            new = df1["volume"].str.split("m", n = 1, expand = True) 
            df1['v'] = new[0]
            
            #Extract the first clashed componenet
            new = df1["comp1"].str.split("\n", n = 1, expand = True) 
            df1['component1'] = new[1]
            
            #Extract the volume
            new = df1["v"].str.split(",", n = 1, expand = True) 
            df1['vol'] = new[1]
            
            #to seperate the component 1 and discipline 1
            new = df1["component1"].str.split("(", n = 1, expand = True) 
            df1['empty1'] = new[0]
            df1['dis1'] = new[1]
            new = df1["dis1"].str.split(")", n = 1, expand = True) 
            df1['discipline1'] = new[0]
            df1['component1'] = new[1]
            
            #to seperate the component 2 and discipline 2
            new = df1["comp2"].str.split("(", n = 1, expand = True) 
            df1['empty'] = new[0]
            df1['dis'] = new[1]
            new = df1["dis"].str.split(")", n = 1, expand = True) 
            df1['discipline2'] = new[0]
            df1['component2'] = new[1]
            
            #Keep only required column in the new dataframe as df and convert the column datatype to numeric
            if "x_axis" in df1:
                df["x_axis"] = pd.to_numeric(df1["x_axis"])
                if "y_axis" in df1:
                    df["y_axis"] = pd.to_numeric(df1["y_axis"])
                    if "z_axis" in df1:
                        df["z_axis"] = pd.to_numeric(df1["z_axis"])
                        if "vol" in df1:
                            df["vol"] = pd.to_numeric(df1["vol"])
                            if "distance2" in df1:
                                df["distance2"] = pd.to_numeric(df1["distance2"])
                                if "distance1" in df1:
                                    df["distance1"] = pd.to_numeric(df1["distance"])
            #feature engineering for ID column 
            df1["Dupli"] = df1.ID.duplicated(keep=False)
            #Encode the values that are not numbers
            #categorical column is encoded using cat.code function.
            df["Location"] = df1.Location
            df["component2"] = df1.component2
            df["component1"] = df1.component1
            df["discipline1"] = df1.discipline2
            df["discipline2"] = df1.discipline2
            df["Clash<1"] = df1.Dupli.astype('category').cat.codes
            df["ID"] = df1["ID"]
            #Adding phase feature
            if phase == "Tender":
                df["phase"] = 1
            elif phase == "Design":
                df["phase"] = 0
            elif phase == "Production":
                df["phase"] = 2
            df["GUID"]=df1["GUID"]
            df = df.dropna(axis = 0, how ='any')
            return df
    except Exception as e:
        print(e)

#Function to encode 
def cat_encode(df):
    df["Location"] = df.Location.astype('category').cat.codes
    df["component2"] = df.component2.astype('category').cat.codes
    df["component1"] = df.component1.astype('category').cat.codes
    df["discipline1"] = df.discipline2.astype('category').cat.codes
    df["discipline2"] = df.discipline2.astype('category').cat.codes
    return df


#function to download a file
def download_link(object_to_download, download_filename, download_link_text):
    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


#sidebar title
st.sidebar.subheader("Application Settings")

#Phase Selection
phase = st.sidebar.selectbox("Select Phase",("Tender", "Design","Production"))

#upload the file using sidebar and file uploader
uploaded_file = st.sidebar.file_uploader(label="Upload a file.",type=['csv','xlsx'])

#condition to upload a file and read the file
global df
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file,engine='openpyxl')
    except Exception as e:
        print(e)

#Display the content of the file
try:
    st.title("Input Data for prediction") 
    st.write(df)
    # Load the model from the file 
    #Load Model
    filename='Model.sav'
    clf =pickle.load(open(filename, 'rb'))
    # # Making predictions 
    #call the data prepration function

    data_preprocessed = prepare_data(df,phase)
    data_check = data_preprocessed.copy()
    data_encode = cat_encode(data_preprocessed)
    data_encode=data_encode.drop(["GUID"],axis=1)
    # # Making predictions 
    d = clf.predict(data_encode)
    proba = clf.predict_proba(data_encode)
    data_check["Predict"] = d
    p = pd.DataFrame(proba, columns = ['proba_0','proba_1'])
    p = p * 100
    data_check["Non-Pseudo Clash Certainity"] = p.proba_0
    data_check["Pseudo Clash Certainity"] = p.proba_1

    st.title("Predicted data with out put column as prediction")
    st.text("0 means open and 1 means resolved for prediction column")
    st.write(data_check)

    #Download df dataframe
    if st.button('Download Dataframe as CSV'):
        tmp_download_link = download_link(data_check, 'YOUR_DF.csv', 'Click here to download your data!')
        st.markdown(tmp_download_link, unsafe_allow_html=True)


    # st.subheader("ROC Curve") 
    # plot_roc_curve(clf, x_test, y_test)
    # st.pyplot()

except Exception as e:
    print(e)
    st.write("Please upload a file to display the contents")



#override the upload size limit
#streamlit run ncc_app.py --server.maxUploadSize=1028
#streamlit run clash_app.py --server.maxUploadSize=1028