import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Collapse
} from '@mui/material';
import {
  CloudUpload,
  Download,
  CheckCircle,
  Error,
  ExpandMore,
  ExpandLess,
  Info
} from '@mui/icons-material';
import { bulkImportUsers } from '../../services/api';

const BulkUserImport = ({ onSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [showErrors, setShowErrors] = useState(false);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await bulkImportUsers(file);
      setResult(response);

      // Call success callback if all users imported successfully
      if (response.errors.length === 0 && onSuccess) {
        setTimeout(() => {
          onSuccess(response);
        }, 2000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to import users');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    // Create CSV template
    const headers = [
      'USERNAME', 'EMAIL', 'FIRSTNAME', 'LASTNAME', 'MI', 'GENDER',
      'EMPID', 'HIREDATE', 'TITLE', 'DIVISION', 'DEPARTMENT', 'LOCATION',
      'JOBCODE', 'MANAGER', 'ADDR1', 'ADDR2', 'CITY', 'STATE', 'ZIP',
      'COUNTRY', 'BIZ_PHONE', 'FAX', 'TIMEZONE', 'DEFAULT_LOCALE', 'STATUS',
      'HR', 'Business Unit', 'REVIEW_FREQ', 'CUSTOM01', 'CUSTOM02',
      'CUSTOM03', 'CUSTOM04', 'CUSTOM05', 'CUSTOM06', 'CUSTOM07',
      'CUSTOM08', 'CUSTOM09', 'CUSTOM10', 'CUSTOM11', 'CUSTOM12',
      'CUSTOM13', 'CUSTOM14', 'CUSTOM15', 'LOGIN_METHOD', 'ASSIGNMENT_ID_EXTERNAL'
    ];

    const example1 = [
      'johndoe', 'john.doe@company.com', 'John', 'Doe', 'M', 'M',
      'EMP001', '1/15/2025', 'Software Engineer', 'Engineering', 'Backend',
      'San Francisco Office', '50000001', 'manager_username',
      '123 Main St', 'Apt 4B', 'San Francisco', 'CA', '94105',
      'United States', '(555) 123-4567', '', 'US/Pacific', 'en_US', 'active',
      'hradmin', 'Technology', 'Annual', 'Senior Engineer', 'Eligible',
      'Engineering', 'Backend', 'Platform', 'Core Services', 'API Team',
      'Company A', 'Regular', '', '', '', '', '', '', '', ''
    ];

    const example2 = [
      'janedoe', 'jane.doe@company.com', 'Jane', 'Smith', 'A', 'F',
      'EMP002', '3/20/2024', 'HR Manager', 'Human Resources', 'Talent Acquisition',
      'New York Office', '40000100', 'NO_MANAGER',
      '456 Park Ave', '', 'New York', 'NY', '10001',
      'United States', '(555) 987-6543', '', 'US/Eastern', 'en_US', 'active',
      '', 'Human Resources', 'Semi-annual', 'Manager', 'Eligible',
      'HR', 'Talent', 'Recruiting', 'Talent Acquisition', 'TA Team',
      'Company A', 'Management', '', '', '', '', '', '', '', ''
    ];

    // Create CSV content
    const csvContent = [
      headers.join(','),
      example1.map(field => `"${field}"`).join(','),
      example2.map(field => `"${field}"`).join(',')
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'user_import_template.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadErrorReport = () => {
    if (!result || result.errors.length === 0) return;

    const csvContent = [
      'Error',
      ...result.errors
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'import_errors.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          Bulk User Import
        </Typography>

        <Typography variant="body2" color="textSecondary" paragraph>
          Upload a CSV file to import multiple users at once. The file must include all mandatory fields.
        </Typography>

        {/* Instructions Section */}
        <Box sx={{ mb: 3 }}>
          <Button
            startIcon={showInstructions ? <ExpandLess /> : <ExpandMore />}
            onClick={() => setShowInstructions(!showInstructions)}
            sx={{ mb: 1 }}
          >
            {showInstructions ? 'Hide' : 'Show'} Import Instructions
          </Button>

          <Collapse in={showInstructions}>
            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
              <Typography variant="subtitle2" gutterBottom>
                <Info fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                CSV File Requirements:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Required Columns"
                    secondary="USERNAME, EMAIL, FIRSTNAME, LASTNAME, GENDER, EMPID, HIREDATE, TITLE, DIVISION, DEPARTMENT, LOCATION, JOBCODE, MANAGER, ADDR1, CITY, STATE, ZIP, COUNTRY, TIMEZONE, DEFAULT_LOCALE, STATUS"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Date Format"
                    secondary="Use MM/DD/YYYY, YYYY-MM-DD, or DD/MM/YYYY for HIREDATE"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Manager Field"
                    secondary="Use existing username or 'NO_MANAGER' if no manager"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Status Field"
                    secondary="Must be 'active' or 'inactive'"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Gender Field"
                    secondary="M, F, Male, Female, Other, or 'Not Specified'"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Unique Fields"
                    secondary="USERNAME, EMAIL, and EMPID must be unique across all users"
                  />
                </ListItem>
              </List>
            </Paper>
          </Collapse>
        </Box>

        {/* Download Template Button */}
        <Box sx={{ mb: 3 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={downloadTemplate}
            fullWidth
            sx={{ mb: 2 }}
          >
            Download CSV Template with Examples
          </Button>
        </Box>

        {/* File Upload Section */}
        <Box sx={{ mb: 3 }}>
          <input
            accept=".csv"
            style={{ display: 'none' }}
            id="csv-file-upload"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="csv-file-upload">
            <Button
              variant="outlined"
              component="span"
              fullWidth
              sx={{ py: 2 }}
            >
              Choose CSV File
            </Button>
          </label>

          {file && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="body2">
                <strong>Selected File:</strong> {file.name}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Size: {(file.size / 1024).toFixed(2)} KB
              </Typography>
            </Box>
          )}
        </Box>

        {/* Upload Button */}
        <Button
          variant="contained"
          color="primary"
          startIcon={<CloudUpload />}
          onClick={handleUpload}
          disabled={!file || uploading}
          fullWidth
          size="large"
          sx={{ mb: 3 }}
        >
          {uploading ? 'Uploading...' : 'Upload and Import Users'}
        </Button>

        {/* Progress Bar */}
        {uploading && (
          <Box sx={{ mb: 3 }}>
            <LinearProgress />
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
              Processing CSV file and creating users...
            </Typography>
          </Box>
        )}

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Success/Results Section */}
        {result && (
          <Box sx={{ mt: 3 }}>
            <Alert
              severity={result.errors.length === 0 ? 'success' : 'warning'}
              sx={{ mb: 2 }}
            >
              <Typography variant="subtitle2" gutterBottom>
                Import Summary
              </Typography>
              <Typography variant="body2">
                Successfully imported: <strong>{result.imported_count}</strong> users
              </Typography>
              {result.errors.length > 0 && (
                <Typography variant="body2" color="error">
                  Errors: <strong>{result.errors.length}</strong>
                </Typography>
              )}
            </Alert>

            {/* Imported Users Table */}
            {result.imported_users.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircle color="success" sx={{ mr: 1 }} />
                  Imported Users ({result.imported_users.length})
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>#</TableCell>
                        <TableCell>Username</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {result.imported_users.map((username, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell>{username}</TableCell>
                          <TableCell>
                            <Chip
                              label="Imported"
                              color="success"
                              size="small"
                              icon={<CheckCircle />}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Errors Section */}
            {result.errors.length > 0 && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Button
                    startIcon={showErrors ? <ExpandLess /> : <ExpandMore />}
                    onClick={() => setShowErrors(!showErrors)}
                    color="error"
                  >
                    <Error sx={{ mr: 1 }} />
                    {showErrors ? 'Hide' : 'Show'} Errors ({result.errors.length})
                  </Button>
                  <Button
                    size="small"
                    startIcon={<Download />}
                    onClick={downloadErrorReport}
                  >
                    Download Error Report
                  </Button>
                </Box>

                <Collapse in={showErrors}>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'error.lighter', maxHeight: 300, overflow: 'auto' }}>
                    <List dense>
                      {result.errors.map((error, index) => (
                        <ListItem key={index}>
                          <Error color="error" fontSize="small" sx={{ mr: 1 }} />
                          <ListItemText
                            primary={error}
                            primaryTypographyProps={{ variant: 'body2', color: 'error' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Collapse>
              </Box>
            )}
          </Box>
        )}

        {/* Help Dialog */}
        <Dialog
          open={showInstructions}
          onClose={() => setShowInstructions(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>CSV Import Instructions</DialogTitle>
          <DialogContent>
            {/* Content moved to Collapse component above */}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowInstructions(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Box>
  );
};

export default BulkUserImport;
