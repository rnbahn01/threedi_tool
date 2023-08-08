from threedi_api_client.threedi_api_client import ThreediApiClient
from threedi_api_client.api import ThreediApi
from threedi_api_client.versions import V3Api
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
import os
import argparse

load_dotenv()

#input your personal API key into the "THREEDI_API_PERSONAL_API_TOKEN"
THREEDI_CONFIG = {
    "THREEDI_API_HOST": os.getenv('THREEDI_API_HOST'),
    "THREEDI_API_PERSONAL_API_TOKEN": os.getenv('THREEDI_API_PERSONAL_API_TOKEN')
} 
ORGANIZATION_UUID = os.getenv('ORGANIZATION_UUID')

def main():
    parser = argparse.ArgumentParser(description='A tool to work with the 3DI API')
    parser.add_argument('--sim_id', type=int, help='This is the ID to your simulation')

    args = parser.parse_args()

    ### BELOW ARE THE FUNCTIONS TO ACTIVATE OR DEACTIVATE, DEPENDING ON WHAT YOU WANT TO DO
    
    THREEDI_API = setup_3di()
    check_models_available(THREEDI_API)
    # my_model, sim = info_on_specific_model(THREEDI_API, os.getenv('MODEL_NAME'), args.sim_id)

    # create_sim(THREEDI_API, my_model)

    ### adding information into your simulation
    # boundary_conditions(THREEDI_API, sim)
    # add_a_breach(THREEDI_API, sim, my_model)
    # add_a_lateral(THREEDI_API, sim, my_model)
    # events(THREEDI_API, sim)

    # run_a_sim(THREEDI_API, sim)

    # check_sim_status(THREEDI_API,sim)
    # delete_model(THREEDI_API, os.getenv('MODEL_NAME'))

    ### downloading your simulation results
    # see_results(THREEDI_API, sim)



def setup_3di(): 
    THREEDI_API = ThreediApi(config=THREEDI_CONFIG, version='v3-beta')
    # try to make sure that login to API is correct
    try:
        user = THREEDI_API.auth_profile_list()
    except:
        print("Failed to sign into 3DI API. Check your API keys?")
        sys.exit()
    else:
        print(f"Successfully logged in as {user.username}!")

    return(THREEDI_API)

#the 'check_models_available' function will print out which 3Di models  of a specific schematisation are available online to run, for academic users, this is limited to 3 models
def check_models_available(THREEDI_API):
    # check which models are available online by replacing the schematisation name 
    models = THREEDI_API.threedimodels_list(name__icontains=os.getenv('SCHEMATISATION_NAME'))
    for model in models.results:
        print(f"{model.name}")

#the 'info_on_specific_model' function will give details about your model.
def info_on_specific_model(THREEDI_API, model_name, sim_id):
    if sim_id == None:
         raise ValueError("The simulation id is required. Pass it in with --sim_id")

    # get info for your specific model 
    models = THREEDI_API.threedimodels_list(name__icontains=model_name)
    my_model = models.results[0]
    print(my_model)

    simulation = THREEDI_API.simulations_list(limit = 50)
   
    for sim in simulation.results:
        if sim.id == sim_id:
            
            return my_model, sim
    
    events = THREEDI_API.simulations_events(sim.id)
    
    print("these are the events:", events)
        
    print("not found")
    return my_model, "not_found"

#the 'create_sim' function creates a new simulation of your model. It will also output the simulation ID which can be used in the next function 'info_on_specific_model'
def create_sim(THREEDI_API, my_model):
    
    my_simulation_template = THREEDI_API.simulation_templates_list(simulation__threedimodel__id=my_model.id).results[0]
    my_simulation = THREEDI_API.simulations_from_template(
            data={
                "template": my_simulation_template.id,
                "name": "2020 terrain, no PS, 2 week sim, breach at 4 hr, T100 WL", #create a name for your simulation
                "organisation": ORGANIZATION_UUID,
                "start_datetime": datetime.now(), #this can be changed to have a different simulation start time
                "duration": 1209600 # in seconds, choose the simulation time
            }
            )
    print(my_simulation)
    print("the simulation id is:" , my_simulation.id)
    return my_simulation

#if you want to delete a model run the function below. 
def delete_model(THREEDI_API, model_name):
    
    model_to_delete = THREEDI_API.threedimodels_list(name__icontains=model_name)
    # my_model = models.results[0]
    delete_model_name = THREEDI_API.threedimodels_delete(model_to_delete)

    print("Deleted:" , f"{delete_model_name.name}")

#the 'boundary_conditions' function allows you to input time varying BC to your simulation. First, it deletes the BC file (if there is already one in place), and then creates a new one based on the .json file you input. In the .json file you decide which node ID to apply the BC to and you can put in the values. 
def boundary_conditions(THREEDI_API, sim):

        BC_file_to_delete = THREEDI_API.simulations_events_boundaryconditions_file_delete(
            simulation_pk = sim.id,
            id = 51351
        )
        boundary_condition_creation = THREEDI_API.simulations_events_boundaryconditions_file_create(
                simulation_pk = sim.id,
                #replace 'boundary_conditions_2weeks.json' with your own time varying boundary condition file (if you use this)
                data={'filename': 'boundary_conditions_2weeks.json'}
            )
        #put the path to your .json boundary condition file as the 'boundary_file' below
        boundary_file = Path("./boundary_conditions_2weeks.json")
        with open(boundary_file, 'rb') as f:
            requests.put(boundary_condition_creation.put_url, data=f)

        events = THREEDI_API.simulations_events(sim.id)
        print(events)

#the function 'add_a_breach' allows you to add a breach as a simulation event. You can specify the breach width, material, etc. The offset is the time (in seconds) after the simulation start and before the breach begins. If you want the breach to begin immediately set offset to zero
def add_a_breach(THREEDI_API, sim, my_model):
    potential_breaches = THREEDI_API.threedimodels_potentialbreaches_list(my_model.id)
    print("these are the potential breaches:", potential_breaches)


    breach = potential_breaches.results[0]
    breach_event = THREEDI_API.simulations_events_breaches_create(
        sim.id, data={
            "potential_breach": breach.id,
            "duration_till_max_depth": 1800,
            "maximum_breach_depth": 3.0,
            "levee_material": "clay",
            "initial_width": 10,
            "offset": 14400
        }
    )

    events = THREEDI_API.simulations_events(sim.id)
    
    print("these are the events:", events)
    print("this is breach event", breach_event)

#the 'add_a_lateral' function allows you to add laterals as a simulation event. Input your For my case, I had three laterals working as pump station. The 'value' is negative so it removes water from the cell. If 'value' is positive, then it would be a source of water to the system.
def add_a_lateral(THREEDI_API, sim, my_model):

    lateral = THREEDI_API.simulations_events_lateral_constant_create(
    sim.id, data={

        "offset": 14400,
        "point": {
            "type": "Point",
            "coordinates": [
            4.8220684, 
            51.8776787 
        ] },
        "value": -1,
        "duration": 417600,
        "units": "m3/s"
    })

    lateral2 = THREEDI_API.simulations_events_lateral_constant_create(
    sim.id, data={
        
            "offset": 14400,
            "point": {
                "type": "Point",
                "coordinates": [
                4.819662, 
                51.877064 
            ] },
            "value": -1,
            "duration": 417600,
            "units": "m3/s"
        })
    
    lateral3 = THREEDI_API.simulations_events_lateral_constant_create(
    sim.id, data={
        "offset": 14400,
        "point": {
            "type": "Point",
            "coordinates": [
            4.818812, 
            51.876807 
        ] },
        "value": -1,
        "duration": 417600,
        "units": "m3/s"
    })
    
    events = THREEDI_API.simulations_events(sim.id)
    
    print("these are the events, including laterals:", events)

#the 'events' function below is useful because you check and see what events you have input into your simulation like rain, laterals, or inital water levels
def events(THREEDI_API, sim):
    events = THREEDI_API.simulations_events(sim.id)
    
    print("these are the events:", events)
    
# 'run_a_sim' will run the simulation through the API. The output from this function should print the status as 'starting'. You can also check the simulation status by running the 'check sim status' function
def run_a_sim(THREEDI_API, sim):

    THREEDI_API.simulations_actions_create(sim.id, data={"name": "start"})

    #check the status of the simulation with:
    status = THREEDI_API.simulations_status_list(sim.id)
    print(status)

    # check if the status is finished
    status = THREEDI_API.simulations_status_list(sim.id)

    print(f"status: {status}")
    assert status.name == 'finished'

#the function below will tell you the status of your simulation. You can check in on it by running this function and it will tell you if it is 'running', 'crashed', or 'finished'
def check_sim_status(THREEDI_API,sim):
    #check the status of the simulation with:
    status = THREEDI_API.simulations_status_list(sim.id) #id number is 113511
    events = THREEDI_API.simulations_events(sim.id)
    
    print("these are the events:", events)
    
    print(status)

#to download the simulation results, first make a results folder in your file explorer. Then put the path to that results folder in line 248, inside the quotations. The results.nc file, gridadmin.h5 file, and aggregate_results.nc file will be downloaded into your designated download folder
def see_results(THREEDI_API, sim):

    result_files = THREEDI_API.simulations_results_files_list(sim.id)

    # download results to local folder, input your path to folder below
    download_folder = Path(f"{os.getenv('DOWNLOAD_FOLDER')}\\{sim.name}")
    download_folder.mkdir(exist_ok=True)

    for file in result_files.results:
        download_url = THREEDI_API.simulations_results_files_download(
            id=file.id, simulation_pk=sim.id
        )

        file_path = download_folder / file.filename
        r = requests.get(download_url.get_url)
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Finished downloading {file.filename}")
        
    # get gridadim file as well

    threedi_model_id = sim.threedimodel_id
    download_url = THREEDI_API.threedimodels_gridadmin_download(threedi_model_id)

    file_path = download_folder / "gridadmin.h5"
    r = requests.get(download_url.get_url)
    with open(file_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Finished downloading gridadmin.h5")

if __name__ == "__main__":
    main()