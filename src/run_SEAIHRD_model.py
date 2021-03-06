###-----------###
### Importing ###
###-----------###
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

from scipy import integrate
import seaborn as sns; sns.set()

###------------------###
### Helper Functions ###
###------------------###

## Time series management
def statal_timeseries(df, log=False):
    '''
    Returns a dataframe with the number of COVID cases where each row is indexed by a date (t0 = 2020-02-28), and each column is a state of Mexico.
    If log=True, return the log of the cases.
    '''
    if log:
        return np.log10( df.drop(['México'], axis=1).set_index('Fecha') )
    else:
        return df.drop(['México'], axis=1).set_index('Fecha')

def national_timeseries(df, log=False):
    '''
    Returns a dataframe with the national number of COVID cases for Mexico where each row is indexed by a date (t0 = 2020-02-28).
    If log=True, return the log of the cases.
    '''
    if log:
        return np.log10( df.set_index('Fecha').loc[:,['México']] )
    else:
        return df.set_index('Fecha').loc[:,['México']]

# mean absolute error
def MAE(x,y): return np.mean(np.abs( x[:] - y[:len(x)] ))

### Solution helper functions
## Time series management
def Suceptibles(sol): return sol[:,0]
def Exposed(sol): return sol[:,1]
def Quarantined(sol): return sol[:,2]
def Asymptomatic(sol): return sol[:,3]
def Infected(sol): return sol[:,4]
def Hospitalized(sol): return sol[:,5]
def Recovered(sol): return sol[:,6]
def Deceased(sol): return sol[:,7]
def ActiveCases(sol): return Infected(sol) + Hospitalized(sol)
def TotalCases(sol): return Infected(sol) + Hospitalized(sol) + Recovered(sol) + Deceased(sol)
def ICUcases(sol): return Hospitalized(sol) + Deceased(sol)
## Aggregation
def CasesAggregation(sol_per_state, f=TotalCases): return np.sum( [f(sol) for sol in sol_per_state], axis=0   )

# takes a set of solutions, aggregates them and saves them in a csv
def scenario_to_csv(filename, sol, initial_date, print_=False):
    '''
    Saves a return a single model output for a given scenario `sol` in a csv
    that contains the dynamics of each compartiment in each column.
    '''
    try:
        # our format
        t0 = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
    except:
        # John Hopkins format
        t0 = datetime.datetime.strptime(initial_date, '%m/%d/%y')

    # this is thought of as a list of arrays
#     (t0 + datetime.timedelta(days=x)).strftime('%d-%m')
    t_range = [t0 + datetime.timedelta(days=x) for x in range( sol[0].shape[0] )]
    CSV = pd.DataFrame(columns=['Fecha','Totales','Infectados','Recuperados','Muertes','Hospitalizados'])

    CSV['Totales'] = CasesAggregation(sol, f=TotalCases)
    CSV['Recuperados'] = CasesAggregation(sol, f=Recovered)
    CSV['Infectados'] = CasesAggregation(sol, f=Infected)
    CSV['Muertes'] = CasesAggregation(sol, f=Deceased)
    CSV['Hospitalizados'] = CasesAggregation(sol, f=Hospitalized)
    CSV['Fecha'] = t_range
    CSV.set_index('Fecha', inplace=True)

    if print_:
        print('Saved projections in {}'.format(filename))

    CSV.to_csv(filename)
    return CSV

def total_cases_scenarios_to_csv(filename, data, scenarios, initial_date, f=TotalCases, R0_index=''):
    '''
    Saves and returns a csv file where the first column 'Totales' presents the available COVID-19 data in
    Mexico to date. The remaining columns are the fits+projections obtained with the model under different
    containtment scenarios.
    '''
    try:
        # our format
        t0 = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
    except:
        # John Hopkins format
        t0 = datetime.datetime.strptime(initial_date, '%m/%d/%y')

    # this is thought of as a list of arrays
    #     (t0 + datetime.timedelta(days=x)).strftime('%d-%m')
    t_range = [(t0 + datetime.timedelta(days=x)).strftime('%Y-%m-%d') for x in range( scenarios[0][0].shape[0] )]


    CSV = pd.DataFrame(columns=['Fecha','Susana_00{}'.format(R0_index),'Susana_20{}'.format(R0_index),'Susana_50{}'.format(R0_index)])

    CSV['Fecha'] = t_range
    CSV.set_index('Fecha', inplace=True)
    CSV.loc[t_range, 'Susana_00{}'.format(R0_index)] = CasesAggregation(scenarios[0], f=f).round().astype('int')
    CSV.loc[t_range, 'Susana_20{}'.format(R0_index)] = CasesAggregation(scenarios[1], f=f).round().astype('int')
    CSV.loc[t_range, 'Susana_50{}'.format(R0_index)] = CasesAggregation(scenarios[2], f=f).round().astype('int')

    # Data = national_timeseries(data)
    # Data['México'] = Data['México'].astype(int)
    # CSV = Data.join(CSV, how='outer')

    if filename != None:
        print('Saved projections in {}'.format(filename))
        CSV.to_csv(filename)

    return CSV

###--------------------###
### PLOTTING FUNCTIONS ###
###--------------------###
def plot_scenarios(filename, projections, data):
    '''
    Plots the projections of the model. `projections` is a pandas DataFrame which columns contain the projection for each containtment scenario with its confidence interval error bars.
    `data` is the raw csv from DATA_URL_MEX and it contains the datapoints of the total confirmed cases in Mexico.
    '''

    plt.figure( figsize=(10,8) )

    # containtment scenario 1 (κ0 = 0.5)
    plt.plot(projections['Susana_50'], lw=3, color='yellow', label='$50 \%$ Susana')
    plt.fill_between(projections.index.values, projections['Susana_50_min'].values, projections['Susana_50_max'].values,
                     alpha=0.2, color='yellow');

    # containtment scenario 2 (κ0 = 0.2)
    plt.plot(projections['Susana_20'], lw=3, color='red', label='$20 \%$ Susana')
    plt.fill_between(projections.index.values, projections['Susana_20_min'].values, projections['Susana_20_max'].values,
    alpha=0.2, color='red');

    # no containtment scenario (κ0 = 0)
    plt.plot(projections['Susana_00'], lw=3, color='blue', label='$0 \%$ Susana')
    plt.fill_between(projections.index.values, projections['Susana_00_min'].values, projections['Susana_00_max'].values,
                     alpha=0.2, color='blue');

    ## Plot total cases data (from 14-march on)
    plt.plot(national_timeseries(data)['2020-03-14':], marker='o', ms=9, lw=0, color='black', alpha=0.7, label='datos')

    ## Plot attributes
    # Susana_20 has shown to be the best fit to date (01-04-2020)
    mae = MAE( national_timeseries(data)['México'], projections['Susana_20'] )

    plt.title( 'Casos totales de COVID-19 en {}. MAE ({}) para la mejor proyección'.format( 'México', (round(mae), 1) ) , size=16)
    plt.ylabel('Número de casos', size=15);
    plt.legend(loc='upper left')
    plt.ylim(-50,  np.minimum( CSV['Susana_00'].max() * 1.25, CSV['Susana_00_max'].max()) )
    # plt.yscale('log')
    plt.xticks(rotation=45)
    plt.tight_layout()

    ## Saving results plot ##
      # NOTE: The following warning appear but it doesn't affect the script:
      # 'Source ID 8 was not found when attempting to remove it GLib.source_remove(self._idle_draw_id)''
    if filename != None:
        plt.savefig(filename)

    return plt.show()

###-------------------------###
### DIRTY FITTING FUNCTIONS ###
###-------------------------###
def solve_national(r, κ0, print_=False):
    '''
    Return the aggregate cases of COVID-19 using our model using a containtment scenario κ0, and a proportion
    `r` of latent infected people.
    This functions assumes that `tc`, `projection_horizon`, `n_days`, `states_mex`,
    and `population_per_state_mex` are already defined in the script.
    '''

    ## Preallocation ##
    # Vectors of solutions. Each vector will contain the results for each state for a specific containtment scenario
    projections_κ0 = []

    for (i, state) in enumerate(states_mex):
        # population for state_i
        N = population_per_state_mex[i]

        # cases for state_i (from data)
        confirmed = statal_timeseries(mex_confirmed).loc[initial_date, state]
        deaths = statal_timeseries(mex_deaths).loc[initial_date, state]
        recovered = statal_timeseries(mex_recovered).loc[initial_date, state]


        ## initial conditions of state_i setup ##
        p = 1/2
        R0 = recovered / N              # fraction of recovered
        D0 = deaths / N                 # fraction of deceased
        I0 = ((confirmed/N) - R0 - D0)  # fraction of confirmed infected cases
        E0 = p*r * I0                 # fraction of exposed non-infectious cases. Latent variable
        A0 = (1-p)*r * I0                 # fraction of asymptomatic but infectious cases. Latent variable
        H0 = 0                          # fraction of hospitalized cases. No data yet
        CH0 = 0                         # fraction of self-isolated cases. 0 if no prevention is made by the government
        S0 = (1 - E0 - A0 - I0 - R0 - D0 - H0) # fraction of suceptible cases

        # inital conditions of state_i
        x0 = np.array([S0, E0, CH0, A0, I0, H0, R0, D0])

        ### MODEL SIMULATIONS FOR VARIOUS CONTAINTMENT SCENARIOS ###
        ## Parameters ###
        params = (β, k_avg, η, α, γI, μI, ν, γH, μH, κ0, σ, tc)

        ### run models for state_i ###
        projection_state_i = solve(SEAIHRD_markov_step, x0, 0.0, n_days, *params) * N

        if print_:
            print('{} has a population of {} people'.format(state, N))
            print('with', (I0 + R0 + D0 + H0)*N, 'total cases.' )

        # Join model simulation for state_i in the vector of solutions
        projections_κ0.append( projection_state_i )

    # Return the total cases at a national level
    return CasesAggregation( projections_κ0 , f=TotalCases)

## r minimization helper functions (dirty)
def f(r): return solve_national(r, 0.0, print_=False)
def cross_validation(data, r_range): return [MAE(data, f(r)) for r in r_range]
def r_min(r_range, mae_range): return r_range[mae_range.index(min(mae_range))]


###------------------###
### Model Definition ###
###------------------###

## Model helper functions
# number of contacts
def k(t, k_avg, κ0, σ, tc): return (1 - κ0*Θ(t,tc))*k_avg + κ0*(σ - 1)*Θ(t,tc)
# probability of not getting infected
def P(I,A, t, β, k_avg, κ0, σ, tc): return 1 - (1-β)**( k(t, k_avg, κ0, σ, tc)*(I+A) )
# heaviside function
def Θ(t,tc): return np.heaviside( t-tc, 1 )
# kronecker delta
def δ(t,tc):
    if t == tc:
        return 1
    else:
        return 0

### Non-compartamental ###
    ## Discrete time Markovian model ##
def SEAIHRD_markov_step(x, t, S_tc, CH_tc, *params):
    '''
    Suceptible (S), Exposed (E), Asymptomatic (A), Infected (I), Hospitalized (H), Recovered (R), Deceased (D) epidemic model.
    The function takes a single time step in the units of days.

    When confinement is present, the model is no longer Markovian as the variables depend on the state of S_tc = S(tc) and CH_tc = CH(tc).
    If tc = np.inf, then no confinement is made.
    '''

    β, k_avg, η, α, γI, μI, ν, γH, μH, *containtment_params = params
    κ0, σ, tc = containtment_params
    S,E,CH,A,I,H,R,D = x

    return [S*(1 - P(I,A, t, β, k_avg, κ0, σ, tc)) * (1 - δ(t,tc)*κ0*CH_tc),     # S(t+1)
            S*P(I,A, t, β, k_avg, κ0, σ, tc) * (1 - δ(t,tc)*κ0*CH_tc) + (1-η)*E, # E(t+1)
            S_tc * κ0 * CH_tc * Θ(t,tc),                                         # CH(t+1)
            η*E + (1-α)*A,                                                       # A(t+1)
            α*A + (1 - (γI+μI+ν))*I,                                             # I(t+1)
            ν*I + (1 - (γH+μH))*H,                                               # H(t+1)
            γI*I + γH*H + R,                                                     # R(t+1)
            μI*I + μH*H + D]                                                     # D(t+1)

### Solver ###
def solve(f, x0, t0, n_steps, *params):
    '''
    Maps the markov chain defined by `f` with initial distribution `x0` at `t0` for `n_steps` steps.
    '''
    xt = [xi for xi in x0]
    sol = np.zeros( (n_steps, len(x0)) )
    S_tc, CH_tc = 0, 0

    (β, k_avg, η, α, γI, μI, ν, γH, μH, κ0, σ, tc) = params

    t = t0
    for (i,t) in enumerate( range(n_steps) ):

        if t == tc:
            S,E,CH,A,I,H,R,D = xt
            S_tc, CH_tc = S, (S + R)**σ

        sol[i,:] = xt

        xt = f(xt, t, S_tc, CH_tc, *params)
        t += 1

    return sol

if __name__ == "__main__":

    ## READING DATA ##
    DATA_URL_MEX = 'https://raw.githubusercontent.com/Juancruzd/Mexico-datos/master/datos/series_de_tiempo/'

    mex_confirmed = pd.read_csv(DATA_URL_MEX+'covid19_mex_casos_totales.csv', )
    mex_deaths = pd.read_csv(DATA_URL_MEX+'covid19_mex_muertes.csv', )
    mex_recovered = pd.read_csv(DATA_URL_MEX+'covid19_mex_recuperados.csv', )

    # preallocation of the CSV with the results of the model
    CSV = pd.DataFrame()

    # paths for saving
    PLOT_PATH = '../media/'
    CSV_PATH  = '../results/'
    save_ = True

    ### PARAMETER ESTIMATION ###
    # population distribution as of 2020ish
    N_mex = 128_569_304 # https://www.worldometers.info/world-population/mexico-population/ (2020-03-34)
    pop_dist_mex = np.array([55545770, 62567894, 9461864])/N_mex
    # population per state in Mexico
    population_per_state_mex = pd.read_csv('../data/poblaciones_estados.csv', index_col=0).sort_index()['population'].values
    # list of states
    states_mex = pd.read_csv('../data/poblaciones_estados.csv', index_col=0).sort_index().index.values

    # Basic reproductive ratio
    # R_0s : 2.3, 95%-CI : (1.4, 3.9), according to Qun Li et al. 'Early Transmission Dynamics in Wuhan, China, ...'
    R0s = {'_min': 1.4, '_max': 3.9, '': 2.3}
    for R0ix in R0s:
        R_0 = R0s[R0ix]
        print('Doing R_0 = {}'.format(R_0))
        ## Arenas params
        β = 0.06 # infectivity of the desease (this value changes for Mexico)
        η = 1/2.34 # η^-1 + α^-1 = 1/5.2 # exposed latent rate
        ωg = 0.42 # fatality rate of ICU patients
        ψg = 1/7  # death rate
        χg = 1/10 # ICU discharge rate
        σ  = 3.7 # average household size in Mexico (different from Arenas)
        μg = np.array([1/1,1/3.2,1/3.2]) # escape (from Infected) rate by age group
        γg = np.array([0.002, 0.05, 0.36]) # fraction of cases requiring ICU by age group
        kg = np.array([11.8, 13.3, 6.6]) # average contacts per day by age group
        αg = np.array([1/5.06, 1/2.86, 1/2.86]) # asymptomatic infectious rate by age group

        ## avering out the age groups with the pyramidal distribution of Mexico
        μ_avg = np.dot(μg, pop_dist_mex)
        γ_avg = np.dot(γg, pop_dist_mex)
        k_avg =  np.dot(kg, pop_dist_mex)
        α = np.dot(αg, pop_dist_mex)

        ## SEAIHRD model params
        β = -np.exp( -R_0/(k_avg * (1/α + 1/μ_avg) ) ) + 1
        k_avg
        η
        α
        γI = μ_avg*(1 - γ_avg)
        μI = 0
        ν = μ_avg*γ_avg
        μH = ωg*ψg
        γH = (1 - ωg)*χg

        ### INITIAL CONDITIONS PER STATE SETUP ###
        # initial date for the model
        initial_date = '2020-03-19' # This is the date in which the trend becomes exponential

        # model projection setup
        tc = 6 # containtment intervention date (days since initial_date)
        projection_horizon = 1 # days
        # number of days to run the model for
        n_days = (datetime.datetime.today() - datetime.datetime.strptime(initial_date, '%Y-%m-%d')).days + projection_horizon

        ### DETERMINING BEST FIT ###
        # We determine r, the proportion of latent E+A individuals by cross'validations. The functions are very dirty at their current states
        r_range = np.linspace(0,2.5, 50) # We've seen empirically that they are not very big
        fit_final_date = '2020-03-28' # officialy, it was implemented on the 25th, but we assume it takes at least 3 days to start seeing the effects.
        data_before_containtment = national_timeseries(mex_confirmed).loc[initial_date:fit_final_date, 'México'].values
        mae_range = cross_validation(data_before_containtment, r_range)
        # Taking best fit
        r = r_min(r_range, mae_range)
        print('r: {}'.format(r))

        ## Preallocation ##
        # Vectors of solutions. Each vector will contain the results for each state for a specific containtment scenario
        projections_susana1 = []
        projections_susana2 = []
        projections_susana3 = []

        print_ = False
        print('Initial date: {}\n'.format(initial_date))
        for (i,state) in enumerate(states_mex):

            # population for state_i
            N = population_per_state_mex[i]

            # cases for state_i (from data)
            confirmed = statal_timeseries(mex_confirmed).loc[initial_date, state]
            deaths = statal_timeseries(mex_deaths).loc[initial_date, state]
            recovered = statal_timeseries(mex_recovered).loc[initial_date, state]

            ## initial conditions of state_i setup ##
            # r = 1 # 0.65 r denotes the fraction of latent cases with respect to the confirmed cases. This is, E0 + A0 = r * I0
            p = 1/2
            R0 = recovered / N              # fraction of recovered
            D0 = deaths / N                 # fraction of deceased
            I0 = ((confirmed/N) - R0 - D0)  # fraction of confirmed infected cases
            E0 = p*r * I0                 # fraction of exposed non-infectious cases. Latent variable
            A0 = (1-p)*r * I0                 # fraction of asymptomatic but infectious cases. Latent variable
            H0 = 0                          # fraction of hospitalized cases. No data yet
            CH0 = 0                         # fraction of self-isolated cases. 0 if no prevention is made by the government
            S0 = (1 - E0 - A0 - I0 - R0 - D0 - H0) # fraction of suceptible cases

            # inital conditions of state_i
            x0 = np.array([S0, E0, CH0, A0, I0, H0, R0, D0])

            ### MODEL SIMULATIONS FOR VARIOUS CONTAINTMENT SCENARIOS ###

            ## Scenario 1: No action
            κ0 = 0.0
            params_1 = (β, k_avg, η, α, γI, μI, ν, γH, μH, κ0, σ, tc)

            ## Scenario 2: Mild distancing
            κ0 = 0.2
            params_2 = (β, k_avg, η, α, γI, μI, ν, γH, μH, κ0, σ, tc)

            ## Scenario 3: Strong distancing
            κ0 = 0.5
            params_3 = (β, k_avg, η, α, γI, μI, ν, γH, μH, κ0, σ, tc)

            ### run models for state_i ###
            projection_state_i_scenario_1 = solve(SEAIHRD_markov_step, x0, 0.0, n_days, *params_1) * N
            projection_state_i_scenario_2 = solve(SEAIHRD_markov_step, x0, 0.0, n_days, *params_2) * N
            projection_state_i_scenario_3 = solve(SEAIHRD_markov_step, x0, 0.0, n_days, *params_3) * N

            ## print summary of results per state if necessary.
            if print_:
                data = statal_timeseries(mex_confirmed).loc[initial_date:,state]
                projection = TotalCases(projection_state_i_scenario_1)
                tf_data = data.index.values[-1]
                print('Projection for {} at {}: {} cases vs {} oficial cases. MAE: ({})'.format( state, tf_data, np.round(projection[-projection_horizon-1]), data.values[-1], round(MAE(data, projection), 1) ))
                print('{} has a population of {} people'.format(state, N))
                print('with', (I0 + R0 + D0 + H0)*N, 'total cases.' )

            # Join model simulation for state_i in the vector of solutions
            projections_susana1.append( projection_state_i_scenario_1 )
            projections_susana2.append( projection_state_i_scenario_2 )
            projections_susana3.append( projection_state_i_scenario_3 )

        # here I construct, for every scenario and every value of R0, a CSV with all the corresponding projections
        scenarios = [projections_susana1, projections_susana2, projections_susana3]
        # first argument = None makes the function to not save the df
        df_ = total_cases_scenarios_to_csv(None, mex_confirmed, scenarios, initial_date, f=TotalCases, R0_index=R0ix)
        CSV = CSV.join(df_, how='outer')

        # Save individual runs with all the compartiments. Not well calibrated for Mexico
        # if save_:
        #     today_date = datetime.datetime.today().strftime('%d-%m-%y')
        #     scenario_to_csv(CSV_PATH+'other/susana_00_{}_R0_{}.csv'.format( today_date, str(R_0).replace('.','p')), projections_susana1, initial_date)
        #     scenario_to_csv(CSV_PATH+'other/susana_20_{}_R0_{}.csv'.format( today_date, str(R_0).replace('.','p')), projections_susana2, initial_date)
        #     scenario_to_csv(CSV_PATH+'other/susana_50_{}_R0_{}.csv'.format( today_date, str(R_0).replace('.','p')), projections_susana3, initial_date)

    ## Creating dataframe with scenarios and error bars ##
    Data = national_timeseries(mex_confirmed)
    Data['México'] = Data['México'].astype(int)
    CSV = Data.join(CSV, how='outer')

    if save_:

        ## Saving results to csv ##
        CSV.to_csv( CSV_PATH+'covid19_mex_proyecciones.csv' )
        plot_scenarios(PLOT_PATH+'covid19_mex_proyecciones.png', CSV, mex_confirmed)

    else:
        print(CSV)
        plot_scenarios(None, CSV, mex_confirmed)

    print('DONE!')
