
import axios, { type AxiosInstance, type AxiosError } from "axios";
import type { AnalysisResponse, PatientFormContext, HealthStatus } from "@/types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined &&
  import.meta.env.VITE_API_BASE_URL !== ""
    ? import.meta.env.VITE_API_BASE_URL
    : "";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000,
  headers: {
    Accept: "application/json",
    "ngrok-skip-browser-warning": "true",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const customError = {
      status: error.response?.status,
      message:
        error.response?.data?.detail ||
        error.message ||
        "An unexpected error occurred while communicating with the backend",
    };

    return Promise.reject(customError);
  }
);

export const healthService = {
  checkHealth: async (): Promise<HealthStatus> => {
    const response = await apiClient.get<HealthStatus>("/health");
    return response.data;
  },
};

export const analysisService = {
  analyzeCase: async (
    imageFile: File,
    context: PatientFormContext
  ): Promise<AnalysisResponse> => {
    const formData = new FormData();

    formData.append("image", imageFile);

    Object.entries(context).forEach(([key, value]) => {
      if (value.trim() !== "") {
        formData.append(key, value);
      }
    });

    const response = await apiClient.post<AnalysisResponse>(
      "/analyze",
      formData
    );

    return response.data;
  },
};

export default apiClient;
