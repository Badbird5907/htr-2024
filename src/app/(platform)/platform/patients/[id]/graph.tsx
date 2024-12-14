"use client";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { ChartConfig, ChartContainer } from "@/components/ui/chart";
import { getEcgData } from "@/server/actions/graph";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import { useEffect, useMemo, useState, useTransition } from "react";
import { TrendingUp } from "lucide-react"
import { calculateMargin, gradientCheck } from "@/lib/math";
import { Input } from "@/components/ui/input";
import { maxDate, minDate, sampleRate, totalSamples, windowSamples } from "@/server/ts/values";
import { Spinner } from "@/components/ui/spinner";
import { Slider } from "@/components/ui/slider";

export const EcgGraph = ({ id }: { id: string }) => {
  const [points, setPoints] = useState<number[]>([]);
  const [step, setStep] = useState(windowSamples / 2);
  const [isPending, startTransition] = useTransition();

  const [margin, setMargin] = useState(0.5);

  useEffect(() => {
    console.log("step", step)
    const debounceTimeout = setTimeout(() => {
      startTransition(async () => {
        await getEcgData(id, step).then((data) => {
          console.log(data)
          setPoints(data);
          setMargin(calculateMargin(data));
        }).catch((error) => {
          console.error(error);
        })
      })
    }, 300); // 300ms debounce delay

    return () => clearTimeout(debounceTimeout);
  }, [step])

  const chartData = useMemo(() => {
    return points.map((point, index) => {
      return {
        x: index * (1000 / sampleRate),
        amplitude: point
      }
    })
  }, [points, step]);
  const detected = useMemo(() => {
    const detected = gradientCheck(points, margin);
    console.log("detected", detected)
    return detected;
  }, [points, margin]);


  const chartConfig = {
    desktop: {
      label: "ECG",
      color: "hsl(var(--chart-1))",
    },
  } satisfies ChartConfig

  return (
    <Card>
      <CardHeader>
        <CardTitle>ECG</CardTitle>
        <CardDescription>
          Electrocardiogram of patient from {minDate.toLocaleTimeString()} to {maxDate.toLocaleTimeString()} ({totalSamples} Data Points)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <AreaChart
            accessibilityLayer
            data={chartData}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="x"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="dot" hideLabel />}
            />
            <Area
              dataKey="amplitude"
              type="linear"
              fill="var(--color-desktop)"
              fillOpacity={0.4}
              stroke="var(--color-desktop)"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex flex-row gap-4">
        <Slider defaultValue={[step - 1]} onValueChange={([value]) => setStep(value ?? (windowSamples / 2))} />
        <Input type="number" className="w-fit" value={margin} onChange={(e) => setMargin(Number(e.target.value))} />
        {detected ? 
          <div className="text-red-500 font-bold">Possible bradycardia detected</div> :
          <div className="text-green-500">Everything looks normal</div>}
      </CardFooter>
    </Card>
  )
}