import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle, Info, MessageSquare, Copy } from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';

const riskConfig = {
  HIGH: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-l-red-500',
    badgeVariant: 'destructive',
  },
  MEDIUM: {
    icon: AlertCircle,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-l-amber-500',
    badgeVariant: 'warning',
  },
  LOW: {
    icon: Info,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-l-green-500',
    badgeVariant: 'secondary',
  },
  BENEFICIAL: {
    icon: CheckCircle,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    borderColor: 'border-l-teal-500',
    badgeVariant: 'outline',
  },
};

export function ClauseRiskCard({ clause, isSelected, onSelect, onAskInChat }) {
  const risk = riskConfig[clause.risk_level] || riskConfig.MEDIUM;
  const RiskIcon = risk.icon;

  const handleCopy = () => {
    navigator.clipboard.writeText(clause.text);
  };

  return (
    <Card
      data-testid="clause-risk-card"
      className={`cursor-pointer transition-all duration-150 border-l-4 ${
        risk.borderColor
      } ${isSelected ? 'ring-2 ring-ring bg-accent/40' : 'hover:bg-muted/60'}`}
      onClick={() => onSelect?.(clause)}
    >
      <CardHeader className="pb-2 pt-4 px-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg ${risk.bgColor}`}>
              <RiskIcon className={`w-4 h-4 ${risk.color}`} />
            </div>
            <h4 className="font-semibold text-sm line-clamp-1">{clause.title}</h4>
          </div>
          <Badge
            variant={risk.badgeVariant}
            className="text-xs shrink-0"
          >
            {clause.risk_level}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4 pt-0 space-y-3">
        {/* Clause text */}
        <p className="text-sm text-muted-foreground line-clamp-3">
          {clause.text}
        </p>

        {/* Explanation */}
        {clause.explanation && (
          <div className="text-sm">
            <span className="font-medium">Analysis: </span>
            <span className="text-muted-foreground line-clamp-2">
              {clause.explanation}
            </span>
          </div>
        )}

        {/* Negotiation suggestion */}
        {clause.negotiation_suggestion && (
          <div className="text-sm bg-muted/50 p-2 rounded-lg">
            <span className="font-medium text-primary">Negotiation tip: </span>
            <span className="text-muted-foreground">
              {clause.negotiation_suggestion}
            </span>
          </div>
        )}

        {/* Meta info and actions */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
            {clause.page_number && <span>Page {clause.page_number}</span>}
            {clause.confidence && (
              <span className="text-muted-foreground">
                {Math.round(clause.confidence * 100)}% confidence
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAskInChat?.(clause);
                    }}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Ask in chat</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy();
                    }}
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Copy text</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
