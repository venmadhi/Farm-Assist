import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Token if available in localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('agrigenie_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Catch Unauthorized errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear invalid token and redirect if needed
      localStorage.removeItem('agrigenie_token');
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: async (fullName, phoneNumber, password, district, soilType, landArea) => {
    const response = await apiClient.post('/auth/register', {
      full_name: fullName,
      phone_number: phoneNumber,
      password,
      location_district: district,
      soil_type: soilType,
      land_area_acres: parseFloat(landArea) || 1.0,
    });
    return response.data;
  },
  
  login: async (phoneNumber, password) => {
    const response = await apiClient.post('/auth/login', {
      phone_number: phoneNumber,
      password,
    });
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('agrigenie_token');
  },
  
  isAuthenticated: () => {
    return !!localStorage.getItem('agrigenie_token');
  }
};

export const twinAPI = {
  getSummary: async () => {
    const response = await apiClient.get('/profile/twin');
    return response.data;
  },
  
  addSoilRecord: async (nitrogen, phosphorus, potassium, ph, organicCarbon = 0.5, boron = 0.2, iron = 4.5, zinc = 0.6) => {
    const response = await apiClient.post('/profile/soil', {
      nitrogen: parseFloat(nitrogen),
      phosphorus: parseFloat(phosphorus),
      potassium: parseFloat(potassium),
      ph: parseFloat(ph),
      organic_carbon: parseFloat(organicCarbon),
      boron: parseFloat(boron),
      iron: parseFloat(iron),
      zinc: parseFloat(zinc)
    });
    return response.data;
  },
  
  addCropHistory: async (cropName, yieldKg, season, year, startDate, endDate, revenue, weatherSummary = null, diseaseIncidence = null, fertilizerUsed = null, marketPrice = null) => {
    const response = await apiClient.post('/profile/crop-history', {
      crop_name: cropName,
      yield_kg: parseFloat(yieldKg),
      season,
      year: parseInt(year),
      start_date: startDate,
      end_date: endDate,
      revenue: parseFloat(revenue) || null,
      weather_summary: weatherSummary,
      disease_incidence: diseaseIncidence,
      fertilizer_used: fertilizerUsed,
      market_price: parseFloat(marketPrice) || null
    });
    return response.data;
  },

  updateFarm: async (farmName, district, lat, lon, soilType, landArea, waterAvail, irrigation) => {
    const response = await apiClient.post('/profile/farm-update', {
      farm_name: farmName,
      location_district: district,
      latitude: parseFloat(lat) || 10.7867,
      longitude: parseFloat(lon) || 76.6548,
      soil_type: soilType,
      land_area_acres: parseFloat(landArea) || 1.0,
      water_availability: waterAvail,
      irrigation_type: irrigation
    });
    return response.data;
  },

  getWeather: async (lat = null, lon = null) => {
    const response = await apiClient.get('/profile/weather', {
      params: { lat, lon }
    });
    return response.data;
  },

  startCropCycle: async (cropName, season, year, areaAcres, expectedYield, expectedProfit, expectedRevenue, startDate = null) => {
    const payload = {
      crop_name: cropName,
      season: season,
      year: parseInt(year),
      area_acres: parseFloat(areaAcres),
      expected_yield: parseFloat(expectedYield),
      expected_profit: parseFloat(expectedProfit),
      expected_revenue: parseFloat(expectedRevenue)
    };
    if (startDate) payload.start_date = startDate;
    const response = await apiClient.post('/profile/crop-cycle', payload);
    return response.data;
  },

  harvestCropCycle: async (cycleId, actualYield, actualPrice, cultivationCost, fertilizerUsed = "", diseaseIncidence = "", startDate = null, harvestDate = null) => {
    const payload = {
      actual_yield: parseFloat(actualYield),
      actual_selling_price: parseFloat(actualPrice),
      cultivation_cost: parseFloat(cultivationCost),
      fertilizer_used: fertilizerUsed,
      disease_incidence: diseaseIncidence
    };
    if (startDate) payload.start_date = startDate;
    if (harvestDate) payload.harvest_date = harvestDate;
    const response = await apiClient.post(`/profile/crop-cycle/${cycleId}/harvest`, payload);
    return response.data;
  },

  getCropCycles: async () => {
    const response = await apiClient.get('/profile/crop-cycles');
    return response.data;
  },

  triggerRetraining: async () => {
    const response = await apiClient.post('/profile/model-retrain');
    return response.data;
  }
};

export const cropAPI = {
  getRecommendation: async (farmId, nitrogen, phosphorus, potassium, ph, organicCarbon = 0.5, boron = 0.2, iron = 4.5, zinc = 0.6, temp = 28.0, humidity = 75.0, rain = 1500.0, season = "Kharif") => {
    const response = await apiClient.post('/crop/recommend', {
      farm_id: parseInt(farmId),
      nitrogen: parseFloat(nitrogen),
      phosphorus: parseFloat(phosphorus),
      potassium: parseFloat(potassium),
      ph: parseFloat(ph),
      organic_carbon: parseFloat(organicCarbon),
      boron: parseFloat(boron),
      iron: parseFloat(iron),
      zinc: parseFloat(zinc),
      temperature: parseFloat(temp) || 28.0,
      humidity: parseFloat(humidity) || 75.0,
      rainfall: parseFloat(rain) || 1500.0,
      season: season
    });
    return response.data;
  },
  
  submitFeedback: async (cropPredictionId, rating, comment, actualOutcome = "pending") => {
    const response = await apiClient.post('/crop/feedback', {
      crop_prediction_id: parseInt(cropPredictionId),
      rating_1_to_5: parseInt(rating),
      comment: comment,
      actual_outcome: actualOutcome,
    });
    return response.data;
  }
};

export const notificationsAPI = {
  getNotifications: async () => {
    const response = await apiClient.get('/notifications/');
    return response.data;
  },
  markAsRead: async (id) => {
    const response = await apiClient.post(`/notifications/${id}/read`);
    return response.data;
  },
  triggerDemo: async () => {
    const response = await apiClient.post('/notifications/trigger-demo');
    return response.data;
  }
};


export const diseaseAPI = {
  scanLeaf: async (imageFile) => {
    const formData = new FormData();
    formData.append('file', imageFile);
    const response = await apiClient.post('/disease/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getHistory: async () => {
    const response = await apiClient.get('/disease/history');
    return response.data;
  }
};

export const fertilizerAPI = {
  calculate: async (farmId, cropName, nitrogen, phosphorus, potassium, ph) => {
    const response = await apiClient.post('/fertilizer/calculate', {
      farm_id: farmId,
      crop_name: cropName,
      nitrogen: parseFloat(nitrogen),
      phosphorus: parseFloat(phosphorus),
      potassium: parseFloat(potassium),
      ph: parseFloat(ph),
    });
    return response.data;
  }
};

export const chatbotAPI = {
  chat: async (message, language = 'AUTO') => {
    const hasMalayalamScript = /[\u0D00-\u0D7F]/u.test(message);
    const requestedLanguage = language === 'ml'
      ? 'MALAYALAM'
      : language === 'en' && !hasMalayalamScript
        ? 'ENGLISH'
        : 'AUTO';
    const response = await apiClient.post('/chatbot/chat', {
      message,
      language: requestedLanguage,
    }, { timeout: 25000 });
    return response.data;
  },

  streamChat: async (message, language = 'AUTO', imageData, onContext, onToken, onError, onComplete) => {
    const hasMalayalamScript = /[\u0D00-\u0D7F]/u.test(message);
    const requestedLanguage = language === 'ml'
      ? 'MALAYALAM'
      : language === 'en' && !hasMalayalamScript
        ? 'ENGLISH'
        : 'AUTO';
    
    const token = localStorage.getItem('agrigenie_token');
    
    try {
      const response = await fetch(`${API_BASE}/chatbot/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          message,
          language: requestedLanguage,
          image_data: imageData || null
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Split by double newline which is the standard SSE separator
        const messages = buffer.split('\n\n');
        
        // Keep the last incomplete message in the buffer
        buffer = messages.pop() || '';
        
        for (const msg of messages) {
          if (msg.startsWith('data: ')) {
            const dataStr = msg.substring(6);
            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'context' && onContext) {
                onContext(data);
              } else if (data.type === 'token' && onToken) {
                onToken(data.text);
              } else if (data.type === 'done' && onComplete) {
                onComplete();
              }
            } catch (e) {
              console.warn('Error parsing SSE JSON:', e);
            }
          }
        }
      }
      
    } catch (err) {
      if (onError) onError(err);
    }
  },

  submitFeedback: async (query, responseText, intent, cropEntity, rating, comment = null) => {
    const response = await apiClient.post('/chatbot/feedback', {
      query,
      response: responseText,
      intent,
      crop_entity: cropEntity,
      rating,
      comment
    });
    return response.data;
  },

  getFeedbackHistory: async () => {
    const response = await apiClient.get('/chatbot/feedback-history');
    return response.data;
  }
};

export const marketAPI = {
  getTrends: async (cropName, district = 'Palakkad') => {
    const response = await apiClient.get('/market/trends', {
      params: { crop: cropName, district }
    });
    return response.data;
  }
};
