"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RefreshCw, Sparkles } from "lucide-react";

interface Price {
  platform: string;
  yes: number;
  no: number;
}

interface Market {
  question: string;
  platformOne: Price;
  platformTwo: Price;
  arbOppo: string;
}

function calculateArb({ yes, no }: { yes: number; no: number }): string {
  console.log(yes, no)

  return (yes + no) > 1 ? "0" : ((1 - (yes + no)) * 100).toFixed(2);
}

function HomePageContent() {
  const [markets, setMarkets] = React.useState<Market[]>([]);

  const refreshMarkets = React.useCallback(async () => {
    const resp = await fetch("http://localhost:5000/matched-events");
    const respJson = (await resp.json()) as any[];

    const newMarkets: Market[] = [];

    respJson.forEach((val) => {
      const platformOne = val[0];
      const platformTwo = val[1];

      const platformOneYes = platformOne.prices ? parseFloat(platformOne.prices[0]) : 0
      const platformOneNo = platformOne.prices ? parseFloat(platformOne.prices[1]) : 0
      const platformTwoYes = platformTwo.prices ? parseFloat(platformTwo.prices[0]) : 0
      const platformTwoNo = platformTwo.prices ? parseFloat(platformTwo.prices[1]) : 0

      newMarkets.push({
        question: platformOne.question,
        platformOne: {
          platform: platformOne.platform,
          yes: platformOneYes,
          no: platformOneNo, 
        },
        platformTwo: {
          platform: platformTwo.platform,
          yes: platformTwoYes,
          no: platformTwoNo,
        },
        arbOppo: calculateArb({
          yes: platformOneYes,
          no: platformTwoNo,
        }),
      });

      // Swap the Yes No calculations
      newMarkets.push({
        question: platformOne.question,
        platformOne: {
          platform: platformTwo.platform,
          yes: platformTwoYes,
          no: platformTwoNo,
        },
        platformTwo: {
          platform: platformOne.platform,
          yes: platformOneYes,
          no: platformOneNo,
        },
        arbOppo: calculateArb({
          yes: platformTwoYes,
          no: platformOneNo, 
        }),
      });
    });

    setMarkets(newMarkets);
  }, []);

  React.useEffect(() => {
    refreshMarkets();
  }, []);

  return (
    <div className="flex-grow">
      <div className="flex flex-row justify-between">
        <h2 className="text-2xl font-bold mb-4 flex items-center">
          <Sparkles className="mr-2 text-yellow-400" />
          Hot Arbs
        </h2>
        <Button variant="secondary" onClick={refreshMarkets}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Hot Arbs
        </Button>
      </div>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {markets.map((val, i) => (
          <Card
            key={`${val.question}-${i}`}
            className="bg-gray-800 border-gray-700 overflow-hidden text-white"
          >
            <CardHeader className="bg-gray-700">
              <CardTitle className="text-lg">{val.question}</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-white">
                  {val.platformOne.platform}
                </span>
                <Badge variant={"secondary"} className="bg-green-600">
                  Yes: {val.platformOne.yes}
                </Badge>
              </div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm text-white">
                  {val.platformTwo.platform}
                </span>
                <Badge variant={"secondary"} className="bg-red-600">
                  No: {val.platformTwo.no}
                </Badge>
              </div>
              <div className="text-center">
                <Badge
                  variant={"outline"}
                  className="bg-purple-600 animate-pulse text-white"
                >
                  {val.arbOppo}% Arb Opportunity
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export { HomePageContent };
