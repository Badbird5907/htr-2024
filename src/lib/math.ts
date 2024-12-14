import { sampleRate } from "@/server/ts/values";

export const gradientCheck = (data: number[], margin: number) => {
  // Calculate gradient and check if dangerous
  let isDangerous = false;

  for (let i = 0; i < data.length - 1; i++) {
    const y1 = data[i];
    const nextY1 = data[i + 1];
    // Calculate gradient (slope) for each pair
    const gradient1 = nextY1 !== undefined && y1 !== undefined 
      ? (nextY1 - y1) / (1 / sampleRate)
      : 0;

    // Check if gradient is out of bounds
    if (Math.abs(gradient1) > margin) {
      isDangerous = true;
      // console.log(`Dangerous gradient detected at index ${i}: gradient1 = ${gradient1}`);
    }
  }
  return isDangerous;
}

export const calculateMargin = (data: number[]): number => {
  let margin = 0;
  for (let i = 0; i < data.length - 1; i++) {
    const y1 = data[i];
    const nextY1 = data[i + 1];
    const gradient1 = nextY1 !== undefined && y1 !== undefined 
      ? (nextY1 - y1) / (1 / sampleRate)
      : 0;
    if (Math.abs(gradient1) > margin) {
      margin = Math.abs(gradient1);
    }
  }
  return margin;
};