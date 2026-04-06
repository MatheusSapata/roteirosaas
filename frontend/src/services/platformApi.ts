import axios from "axios";
import { PLATFORM_API_BASE_URL } from "../utils/apiBase";

const platformApi = axios.create({
  baseURL: PLATFORM_API_BASE_URL
});

export default platformApi;
