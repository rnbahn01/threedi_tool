### Setup

1. Clone the repo
2. `cd threedi_tool`
3. `cp .env.example .env`
4. Fill in the environment variables
5. `3Di_API.py --sim_id 134382`

### Things to note

The example .json file I sent is for WL time varying. The first value is seconds and the next value is WL in meters.

### Usage

Once you get familiar with what each function does in the script (I tried to describe each one before it is called), then the functions can be called within the main() function at the beginning.

To use a function, uncomment the function within the main() function

For example if you want to create a new simulation (create_sim) you would also need to run setup_3di and info_on_specific_model functions because they define the THREEDI_API, my_model that 'create_sim' requires.

Once a simulation is created, edited (optional, to add laterals, boundary conditions, etc.), and run then the results can be downloaded using the 'see_results' function.