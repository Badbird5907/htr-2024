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
  const [ecgPoints, setEcgPoints] = useState<number[]>([]);
  const [respPoints, setRespPoints] = useState<number[]>([]);
  const [step, setStep] = useState(windowSamples / 2);
  const [isPending, startTransition] = useTransition();

  const [margin, setMargin] = useState(0.5);

  const fetchData = async () => {
    return getEcgData(id, step).then((data) => {
      console.log(data)
      setEcgPoints(data.ecg);
      setRespPoints(data.resp);
      setMargin(calculateMargin(data.ecg));
    }).catch((error) => {
      console.error(error);
    })
  }

  useEffect(() => {
    console.log("step", step)
    const debounceTimeout = setTimeout(() => {
      startTransition(async () => {
        await fetchData();
      })
    }, 300); // 300ms debounce delay

    return () => clearTimeout(debounceTimeout);
  }, [step])

  const ecgChartData = useMemo(() => {
    return ecgPoints.map((point, index) => {
      return {
        x: index * (1000 / sampleRate),
        amplitude: point
      }
    })
  }, [ecgPoints, step]);
  const respChartData = useMemo(() => {
    return respPoints.map((point, index) => {
      return {
        x: index * (1000 / sampleRate),
        amplitude: point
      }
    })
  }, [respPoints, step]);
  const detected = useMemo(() => {
    const detected = gradientCheck(ecgPoints, margin);
    console.log("detected", detected)
    return detected;
  }, [ecgPoints, margin]);


  const chartConfig = {
    desktop: {
      label: "ECG",
      color: "hsl(var(--chart-1))",
    },
  } satisfies ChartConfig

  return (
    <>
      <Card className="w-full">
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
              data={ecgChartData}
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
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Respitory</CardTitle>
          <CardDescription>
            Respiratory rate of patient from {minDate.toLocaleTimeString()} to {maxDate.toLocaleTimeString()} ({totalSamples} Data Points)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfig}>
            <AreaChart
              accessibilityLayer
              data={respChartData}
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
      </Card>
    </>
  )
}