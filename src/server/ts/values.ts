export const minDate = new Date(
  "2024-12-14T22:04:51.760Z"
)
export const maxDate = new Date(
  "2024-12-14T22:07:21.720Z"
)
export const seconds = (maxDate.getTime() - minDate.getTime()) / 1000
export const sampleRate = 250
export const totalSamples = seconds * sampleRate

export const windowSize = 15; // seconds
export const windowSamples = windowSize * sampleRate;


