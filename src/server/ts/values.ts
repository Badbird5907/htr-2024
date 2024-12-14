export const minDate = new Date(
  "2024-12-14T22:50:02.829Z"
)
export const maxDate = new Date(
  "2024-12-14T22:52:32.789Z"
)
export const seconds = (maxDate.getTime() - minDate.getTime()) / 1000
export const sampleRate = 250
export const totalSamples = seconds * sampleRate

export const windowSize = 5; // seconds
export const windowSamples = windowSize * sampleRate;


