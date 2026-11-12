import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, FileText, Trash2, ExternalLink, Search, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { useAnalysisStore } from '../store/analysisStore';
import { analyzeApi } from '../services/api';
import { toast } from 'sonner';

export default function Dashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const { documents, setDocuments, setCurrentDocument, setCurrentAnalysis } = useAnalysisStore();

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await analyzeApi.listDocuments();
      if (response.data.success) {
        setDocuments(response.data.documents);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, [setDocuments]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleOpenDocument = (doc) => {
    setCurrentDocument(doc);
    setCurrentAnalysis(null);
    navigate(`/analysis/${doc.document_id}`);
  };

  const handleDelete = async () => {
    if (!deletingId) return;

    try {
      await analyzeApi.deleteDocument(deletingId);
      setDocuments(documents.filter((d) => d.document_id !== deletingId));
      toast.success('Document deleted');
    } catch (err) {
      toast.error('Failed to delete document');
    } finally {
      setDeleteDialogOpen(false);
      setDeletingId(null);
    }
  };

  const filteredDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(search.toLowerCase())
  );

  const riskBadgeVariant = (rating) => {
    if (rating === 'Good') return 'secondary';
    if (rating === 'Bad') return 'destructive';
    return 'warning';
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-semibold mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              Manage your analyzed documents
            </p>
          </div>
          <Link to="/upload">
            <Button data-testid="documents-open-button">
              <Plus className="w-4 h-4 mr-2" />
              New Analysis
            </Button>
          </Link>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 max-w-md"
            data-testid="documents-search-input"
          />
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : filteredDocuments.length === 0 ? (
          <Card className="py-20">
            <CardContent className="text-center">
              <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="text-xl font-semibold mb-2">
                {search ? 'No matching documents' : 'No documents yet'}
              </h3>
              <p className="text-muted-foreground mb-6">
                {search
                  ? 'Try a different search term'
                  : 'Upload your first finance agreement to get started'}
              </p>
              {!search && (
                <Link to="/upload">
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Upload Document
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <Table data-testid="documents-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Analyzed</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocuments.map((doc) => (
                  <TableRow
                    key={doc.document_id}
                    className="cursor-pointer"
                    onClick={() => handleOpenDocument(doc)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                          <FileText className="w-4 h-4 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium truncate max-w-[300px]">
                            {doc.filename}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {doc.page_count} pages
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{doc.document_type}</Badge>
                    </TableCell>
                    <TableCell>
                      {doc.has_analysis ? (
                        <div className="flex items-center gap-2">
                          <Badge variant={riskBadgeVariant(doc.rating)}>
                            {doc.rating || 'N/A'}
                          </Badge>
                          {doc.risk_score !== undefined && (
                            <span className="text-sm font-mono">
                              {doc.risk_score.toFixed(1)}/10
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">Not analyzed</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {doc.analyzed_at
                        ? new Date(doc.analyzed_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenDocument(doc);
                          }}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingId(doc.document_id);
                            setDeleteDialogOpen(true);
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Document?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the document and all its analysis data.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
