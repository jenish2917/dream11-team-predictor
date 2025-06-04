import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import Select from 'react-select';
import MainLayout from '../components/layout/MainLayout';
import { predictionService } from '../services/api';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [recentMatches, setRecentMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [dataUpdateLoading, setDataUpdateLoading] = useState(false);
  
  // React Hook Form setup
  const { register, handleSubmit, control, formState: { errors }, watch } = useForm({
    defaultValues: {
      team1: '',
      team2: '',
      venue: '',
      pitchCondition: '',
      date: new Date().toISOString().slice(0, 10) // Default to current date
    }
  });

  // Watch team1 value to ensure team2 is different
  const watchTeam1 = watch('team1');

  // Sample data for form fields with format for react-select
  const teams = [
    { value: '1', label: 'Mumbai Indians' },
    { value: '2', label: 'Chennai Super Kings' },
    { value: '3', label: 'Royal Challengers Bangalore' },
    { value: '4', label: 'Kolkata Knight Riders' },
    { value: '5', label: 'Delhi Capitals' },
    { value: '6', label: 'Rajasthan Royals' },
    { value: '7', label: 'Sunrisers Hyderabad' },
    { value: '8', label: 'Punjab Kings' },
    { value: '9', label: 'Gujarat Titans' },
    { value: '10', label: 'Lucknow Super Giants' }
  ];

  const venues = [
    { value: '1', label: 'Mumbai - Wankhede Stadium' },
    { value: '2', label: 'Chennai - M.A. Chidambaram Stadium' },
    { value: '3', label: 'Bangalore - M. Chinnaswamy Stadium' },
    { value: '4', label: 'Kolkata - Eden Gardens' },
    { value: '5', label: 'Delhi - Arun Jaitley Stadium' },
    { value: '6', label: 'Ahmedabad - Narendra Modi Stadium' },
    { value: '7', label: 'Hyderabad - Rajiv Gandhi International Stadium' },
    { value: '8', label: 'Mohali - IS Bindra Stadium' },
    { value: '9', label: 'Jaipur - Sawai Mansingh Stadium' },
    { value: '10', label: 'Lucknow - BRSABV Ekana Cricket Stadium' }
  ];

  const pitchConditions = [
    { value: 'BAT', label: 'Batting Friendly' },
    { value: 'BWL', label: 'Bowling Friendly' },
    { value: 'BAL', label: 'Balanced' },
    { value: 'SPIN', label: 'Spin Friendly' }
  ];

  // Custom styles for react-select
  const selectStyles = {
    control: (base, state) => ({
      ...base,
      borderColor: '#d1d5db',
      boxShadow: state.isFocused ? '0 0 0 2px rgba(16, 185, 129, 0.2)' : 'none',
      '&:hover': {
        borderColor: state.isFocused ? '#10b981' : '#9ca3af'
      },
      borderRadius: '0.375rem',
      padding: '2px'
    }),
    option: (base, { isSelected, isFocused }) => ({
      ...base,
      backgroundColor: isSelected 
        ? '#10b981' 
        : isFocused 
            ? 'rgba(16, 185, 129, 0.1)'
            : undefined,
      color: isSelected ? 'white' : undefined,
      '&:active': {
        backgroundColor: '#047857'
      }
    })
  };
  const onSubmit = async (data) => {
    setLoading(true);
    
    try {
      // Format data from form to match API expectations
      const formattedData = {
        team1: data.team1.value,
        team2: data.team2.value,
        venue: data.venue.value,
        pitchCondition: data.pitchCondition.value,
        updateData: data.updateData || false
      };
      
      // Make actual API call to generate predictions
      const response = await predictionService.predictTeam(formattedData);
      
      // Navigate to prediction results page with the prediction ID
      navigate(`/prediction-results/${response.id}`, { state: { prediction: response } });
    } catch (err) {
      console.error("Error generating prediction:", err);
      alert('Failed to generate prediction. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const updatePlayerData = async () => {
    setDataUpdateLoading(true);
    try {
      const response = await predictionService.updatePlayerData();
      alert('Player data update initiated. This may take a few minutes.');
      checkPipelineStatus();
    } catch (err) {
      console.error("Error updating player data:", err);
      alert('Failed to update player data. Please try again.');
    } finally {
      setDataUpdateLoading(false);
    }
  };
  
  const checkPipelineStatus = async () => {
    try {
      const status = await predictionService.checkPipelineStatus();
      setPipelineStatus(status);
    } catch (err) {
      console.error("Error checking pipeline status:", err);
    }
  };
  // Fetch recent matches and pipeline status
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch recent matches
        const data = await predictionService.getUserHistory();
        setRecentMatches(data.slice(0, 3));
        
        // Fetch pipeline status
        await checkPipelineStatus();
      } catch (err) {
        console.error("Error fetching initial data:", err);
      } finally {
        setLoadingMatches(false);
      }
    };

    fetchInitialData();
  }, []);

  return (
    <MainLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6 dark:text-white">Dream11 Team Predictor</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prediction Form */}          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold dark:text-white">Generate Prediction</h2>
                
                {pipelineStatus && (
                  <div className="flex items-center">
                    <span className="text-sm mr-2 dark:text-gray-300">Data Status:</span>
                    {pipelineStatus.data_collection ? (
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Up to date</span>
                    ) : (
                      <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">Update recommended</span>
                    )}
                  </div>
                )}
              </div>
              
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Team 1 Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Team 1
                    </label>
                    <Controller
                      name="team1"
                      control={control}
                      rules={{ required: "Team 1 is required" }}
                      render={({ field }) => (
                        <Select
                          {...field}
                          options={teams}
                          styles={selectStyles}
                          placeholder="Select first team"
                          className="text-gray-800"
                          isSearchable
                        />
                      )}
                    />
                    {errors.team1 && (
                      <p className="mt-1 text-sm text-red-600">{errors.team1.message}</p>
                    )}
                  </div>
                  
                  {/* Team 2 Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Team 2
                    </label>
                    <Controller
                      name="team2"
                      control={control}
                      rules={{ 
                        required: "Team 2 is required",
                        validate: value => 
                          !watchTeam1 || value.value !== watchTeam1.value || "Teams cannot be the same"
                      }}
                      render={({ field }) => (
                        <Select
                          {...field}
                          options={teams}
                          styles={selectStyles}
                          placeholder="Select second team"
                          className="text-gray-800"
                          isSearchable
                        />
                      )}
                    />
                    {errors.team2 && (
                      <p className="mt-1 text-sm text-red-600">{errors.team2.message}</p>
                    )}
                  </div>
                  
                  {/* Venue Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Venue
                    </label>
                    <Controller
                      name="venue"
                      control={control}
                      rules={{ required: "Venue is required" }}
                      render={({ field }) => (
                        <Select
                          {...field}
                          options={venues}
                          styles={selectStyles}
                          placeholder="Select venue"
                          className="text-gray-800"
                          isSearchable
                        />
                      )}
                    />
                    {errors.venue && (
                      <p className="mt-1 text-sm text-red-600">{errors.venue.message}</p>
                    )}
                  </div>
                  
                  {/* Pitch Condition */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Pitch Condition
                    </label>
                    <Controller
                      name="pitchCondition"
                      control={control}
                      rules={{ required: "Pitch condition is required" }}
                      render={({ field }) => (
                        <Select
                          {...field}
                          options={pitchConditions}
                          styles={selectStyles}
                          placeholder="Select pitch condition"
                          className="text-gray-800"
                        />
                      )}
                    />
                    {errors.pitchCondition && (
                      <p className="mt-1 text-sm text-red-600">{errors.pitchCondition.message}</p>
                    )}
                  </div>
                  
                  {/* Date Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Match Date
                    </label>
                    <input
                      type="date"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      {...register("date", { required: "Match date is required" })}
                    />
                    {errors.date && (
                      <p className="mt-1 text-sm text-red-600">{errors.date.message}</p>
                    )}
                  </div>                </div>
                
                {/* Force Data Update */}
                <div className="flex items-center mt-4">
                  <input
                    type="checkbox"
                    id="updateData"
                    {...register('updateData')}
                    className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                  />
                  <label htmlFor="updateData" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                    Force data update during prediction (takes longer)
                  </label>
                </div>
                
                {/* Submit Button */}
                <div className="flex justify-between items-center mt-6">
                  <button
                    type="button"
                    onClick={updatePlayerData}
                    disabled={dataUpdateLoading}
                    className={`
                      ${dataUpdateLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'}
                      text-white px-4 py-2 rounded-md text-sm transition-colors duration-200
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
                      flex items-center
                    `}
                  >
                    {dataUpdateLoading && (
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    )}
                    {dataUpdateLoading ? 'Updating Players...' : 'Update Player Data'}
                  </button>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className={`
                      ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600'}
                      text-white px-6 py-2 rounded-md font-medium transition-colors duration-200
                      focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50
                      flex items-center
                    `}
                  >
                    {loading && (
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    )}
                    {loading ? 'Generating...' : 'Generate Prediction'}
                  </button>
                </div>
              </form>
            </div>
          </div>
          
          {/* Recent Predictions */}
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 h-full">
              <h2 className="text-xl font-semibold mb-4 dark:text-white">Recent Predictions</h2>
              
              {loadingMatches ? (
                <div className="flex items-center justify-center h-48">
                  <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-green-500"></div>
                </div>
              ) : recentMatches.length === 0 ? (
                <div className="flex items-center justify-center h-48 text-gray-500 dark:text-gray-400">
                  <div className="text-center">
                    <p>No predictions yet</p>
                    <p className="text-sm">Make your first prediction!</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentMatches.map((match, index) => (
                    <div 
                      key={match.id} 
                      className="p-4 border rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-700 cursor-pointer transition-colors duration-150"
                      onClick={() => navigate(`/prediction-results/${match.id}`)}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="font-medium dark:text-white">{match.team1} vs {match.team2}</h3>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(match.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-300">
                        <div className="flex items-center space-x-1">
                          <span className="material-icons text-xs">location_on</span>
                          <span>{match.venue}</span>
                        </div>
                        <div className="flex items-center space-x-1 mt-1">
                          <span className="material-icons text-xs">sports_cricket</span>
                          <span>{match.team_type || 'Balanced'} Team</span>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  <div className="flex justify-center mt-2">
                    <button 
                      className="text-green-500 hover:text-green-700 text-sm font-medium dark:text-green-400 dark:hover:text-green-300"
                      onClick={() => navigate('/history')}
                    >
                      View All Predictions
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default DashboardPage;
