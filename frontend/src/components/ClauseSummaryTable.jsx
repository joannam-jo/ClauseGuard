import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ChevronDown, Filter } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { ScrollArea } from '../components/ui/scroll-area';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RISK_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2, BENEFICIAL: 3 };

const RISK_BADGE_VARIANT = {
  HIGH: 'destructive',
  MEDIUM: 'warning',
  LOW: 'secondary',
  BENEFICIAL: 'outline',
};

const RISK_FILTER_OPTIONS = [
  { value: 'all', label: 'All Risks' },
  { value: 'HIGH', label: 'High Risk Only' },
  { value: 'MEDIUM', label: 'Medium Risk Only' },
  { value: 'LOW', label: 'Low Risk Only' },
  { value: 'BENEFICIAL', label: 'Beneficial Only' },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ClauseStatsBar({ clauses, riskCounts }) {
  return (
    <div className="flex items-center gap-4 text-sm">
      <span className="text-muted-foreground">Total: {clauses.length} clauses</span>
      <div className="flex gap-2">
        <Badge variant="destructive" className="text-xs">
          {riskCounts.HIGH} High
        </Badge>
        <Badge variant="warning" className="text-xs">
          {riskCounts.MEDIUM} Medium
        </Badge>
        <Badge variant="secondary" className="text-xs">
          {riskCounts.LOW} Low
        </Badge>
        <Badge variant="outline" className="text-xs">
          {riskCounts.BENEFICIAL} Beneficial
        </Badge>
      </div>
    </div>
  );
}

function RiskFilterMenu({ filterRisk, onFilterChange }) {
  const currentLabel =
    RISK_FILTER_OPTIONS.find((o) => o.value === filterRisk)?.label ?? 'All Risks';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" data-testid="clause-table-filter">
          <Filter className="w-4 h-4 mr-1" />
          {currentLabel}
          <ChevronDown className="w-4 h-4 ml-1" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        {RISK_FILTER_OPTIONS.map((opt) => (
          <DropdownMenuItem key={opt.value} onClick={() => onFilterChange(opt.value)}>
            {opt.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function SortableHeader({ field, label, onToggle, testId }) {
  return (
    <TableHead>
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => onToggle(field)}
        data-testid={testId}
      >
        {label}
        <ArrowUpDown className="w-3 h-3 ml-1" />
      </Button>
    </TableHead>
  );
}

// ---------------------------------------------------------------------------
// Sorting helpers
// ---------------------------------------------------------------------------

function compareClauses(a, b, sortBy) {
  if (sortBy === 'risk') return (RISK_ORDER[a.risk_level] ?? 99) - (RISK_ORDER[b.risk_level] ?? 99);
  if (sortBy === 'page') return (a.page_number ?? 999) - (b.page_number ?? 999);
  if (sortBy === 'confidence') return (b.confidence ?? 0) - (a.confidence ?? 0);
  return 0;
}

function computeRiskCounts(clauses) {
  const counts = { HIGH: 0, MEDIUM: 0, LOW: 0, BENEFICIAL: 0 };
  clauses.forEach((c) => {
    if (c.risk_level in counts) counts[c.risk_level]++;
  });
  return counts;
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export function ClauseSummaryTable({ clauses = [], onClauseSelect, selectedClauseId }) {
  const [sortBy, setSortBy] = useState('risk');
  const [sortOrder, setSortOrder] = useState('asc');
  const [filterRisk, setFilterRisk] = useState('all');

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const sortedClauses = useMemo(() => {
    const filtered =
      filterRisk === 'all' ? [...clauses] : clauses.filter((c) => c.risk_level === filterRisk);
    filtered.sort((a, b) => {
      const cmp = compareClauses(a, b, sortBy);
      return sortOrder === 'asc' ? cmp : -cmp;
    });
    return filtered;
  }, [clauses, sortBy, sortOrder, filterRisk]);

  const riskCounts = useMemo(() => computeRiskCounts(clauses), [clauses]);

  return (
    <div className="space-y-3" data-testid="clause-summary-table">
      <ClauseStatsBar clauses={clauses} riskCounts={riskCounts} />

      <div className="flex items-center gap-2">
        <RiskFilterMenu filterRisk={filterRisk} onFilterChange={setFilterRisk} />
      </div>

      <ScrollArea className="h-[400px] rounded-md border">
        <Table className="clause-table">
          <TableHeader className="sticky top-0 bg-card z-10">
            <TableRow>
              <SortableHeader field="title" label="Clause" onToggle={toggleSort} />
              <SortableHeader
                field="risk"
                label="Risk"
                onToggle={toggleSort}
                testId="clause-table-sort-risk"
              />
              <SortableHeader field="page" label="Page" onToggle={toggleSort} />
              <SortableHeader field="confidence" label="Confidence" onToggle={toggleSort} />
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedClauses.map((clause) => (
              <TableRow
                key={clause.clause_id}
                className={selectedClauseId === clause.clause_id ? 'selected' : ''}
                onClick={() => onClauseSelect?.(clause)}
              >
                <TableCell className="font-medium">
                  <span className="line-clamp-1">{clause.title}</span>
                </TableCell>
                <TableCell>
                  <Badge variant={RISK_BADGE_VARIANT[clause.risk_level] ?? 'secondary'}>
                    {clause.risk_level}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-sm">
                  {clause.page_number ?? '-'}
                </TableCell>
                <TableCell className="font-mono text-sm">
                  {clause.confidence ? `${Math.round(clause.confidence * 100)}%` : '-'}
                </TableCell>
              </TableRow>
            ))}
            {sortedClauses.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                  No clauses found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </ScrollArea>
    </div>
  );
}
