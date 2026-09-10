import axios from 'axios'

const BASE_URL = '/api'

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

export function updatePushSetting(pushEnable) {
  const token = localStorage.getItem('access_token')

  return axios.put(
    `${BASE_URL}/auth/push-setting`,
    {
      push_enable: pushEnable
    },
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )
}

export function updatePassword(
  currentPassword,
  newPassword
) {
  const token =
    localStorage.getItem('access_token')

  return axios.put(
    `${BASE_URL}/auth/password`,
    {
      current_password: currentPassword,
      new_password: newPassword
    },
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )
}

export function updatePhone(phone) {
  const token =
    localStorage.getItem('access_token')

  return axios.put(
    `${BASE_URL}/auth/phone`,
    {
      phone: phone
    },
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )
}

export function updateLocation(lng, lat) {
  const token =
    localStorage.getItem('access_token')

  return axios.put(
    `${BASE_URL}/auth/location`,
    {
      lng: lng,
      lat: lat
    },
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )
}