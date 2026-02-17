// Mock API wrapper - In prod use axios
const BASE_URL = "/api/v1/search";

export const searchRealEstate = async (params) => {
  // Convert object to query string
  const query = new URLSearchParams();
  
  // Defaults
  query.append("country", "DE"); // Hardcoded for MVP if not provided
  
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.append(key, value);
  });

  try {
    const response = await fetch(`${BASE_URL}/real-estate?${query.toString()}`);
    if (!response.ok) throw new Error("Search failed");
    return await response.json();
  } catch (error) {
    console.error("API Error:", error);
    // Return empty structure on error to prevent UI crash
    return { data: [], meta: { count: 0 } };
  }
};
