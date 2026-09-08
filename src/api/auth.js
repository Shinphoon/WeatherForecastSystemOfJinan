import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000'

export function registerUser(data) {
  return axios.post(
    `${BASE_URL}/auth/register`,
    data
  )
}

export function loginUser(data) {
  return axios.post(
    `${BASE_URL}/auth/login`,
    data
  )
}

export function getCurrentUser() {
  const token =
    localStorage.getItem('access_token')

  return axios.get(
    `${BASE_URL}/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )
}