export const minDate = new Date(
  "2024-12-14T22:40:25.516Z"
)
export const maxDate = new Date(
  "2024-12-14T22:40:25.516Z"
)
export const seconds = (maxDate.getTime() - minDate.getTime()) / 1000
export const sampleRate = 250
export const totalSamples = seconds * sampleRate

export const windowSize = 15; // seconds
export const windowSamples = windowSize * sampleRate;


