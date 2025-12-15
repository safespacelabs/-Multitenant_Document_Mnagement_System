import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Alert,
  CircularProgress,
  FormHelperText,
  Divider
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { createExtendedUser } from '../../services/api';

const ExtendedUserForm = ({ onSuccess, onCancel }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    // Basic Identity
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    middle_initial: '',
    gender: 'Not Specified',
    display_name: '',

    // Employment
    employee_id: '',
    hire_date: new Date(),
    title: '',
    division: '',
    department: '',
    location: '',
    job_code: '',
    manager: 'NO_MANAGER',
    role: 'employee',
    hr: '',
    business_unit: '',
    matrix_manager: '',
    second_manager: '',
    custom_manager: '',

    // Address
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'United States',
    business_phone: '',
    business_fax: '',

    // System
    timezone: 'US/Pacific',
    default_locale: 'en_US',
    status: 'active',

    // Review
    review_frequency: '',
    last_review_date: null,

    // Custom Fields
    custom01: '', // Career Level
    custom02: '', // Eligibility Flag
    custom03: '', // L04 Org Unit
    custom04: '', // L05 Org Unit
    custom05: '', // L06 Org Unit
    custom06: '', // L07 Org Unit
    custom07: '', // L08 Org Unit
    custom08: '', // Company
    custom09: '', // EESubgroup
    custom10: '', // Union
    custom11: '',
    custom12: '',
    custom13: '',
    custom14: '',
    custom15: '',

    // Auth
    login_method: '',
    proxy: '',
    assignment_id_external: ''
  });

  const [errors, setErrors] = useState({});

  const steps = [
    'Basic Information',
    'Employment Details',
    'Address & Contact',
    'Additional Details'
  ];

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    });
    // Clear error for this field
    if (errors[field]) {
      setErrors({ ...errors, [field]: null });
    }
  };

  const handleDateChange = (field) => (date) => {
    setFormData({
      ...formData,
      [field]: date
    });
  };

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 0: // Basic Information
        if (!formData.username) newErrors.username = 'Username is required';
        if (!formData.email) newErrors.email = 'Email is required';
        if (!formData.first_name) newErrors.first_name = 'First name is required';
        if (!formData.last_name) newErrors.last_name = 'Last name is required';
        if (!formData.gender) newErrors.gender = 'Gender is required';
        if (!formData.employee_id) newErrors.employee_id = 'Employee ID is required';
        break;

      case 1: // Employment Details
        if (!formData.title) newErrors.title = 'Job title is required';
        if (!formData.division) newErrors.division = 'Division is required';
        if (!formData.department) newErrors.department = 'Department is required';
        if (!formData.location) newErrors.location = 'Location is required';
        if (!formData.job_code) newErrors.job_code = 'Job code is required';
        if (!formData.hire_date) newErrors.hire_date = 'Hire date is required';
        break;

      case 2: // Address & Contact
        if (!formData.address_line1) newErrors.address_line1 = 'Address is required';
        if (!formData.city) newErrors.city = 'City is required';
        if (!formData.state) newErrors.state = 'State is required';
        if (!formData.zip_code) newErrors.zip_code = 'ZIP code is required';
        if (!formData.country) newErrors.country = 'Country is required';
        break;

      case 3: // Additional Details (optional)
        // No required fields
        break;

      default:
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(activeStep)) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Format data for API
      const submitData = {
        ...formData,
        hire_date: formData.hire_date ? formData.hire_date.toISOString().split('T')[0] : null,
        last_review_date: formData.last_review_date ? formData.last_review_date.toISOString().split('T')[0] : null,
        // Remove empty optional fields
        middle_initial: formData.middle_initial || undefined,
        display_name: formData.display_name || undefined,
        address_line2: formData.address_line2 || undefined,
        business_phone: formData.business_phone || undefined,
        business_fax: formData.business_fax || undefined,
        hr: formData.hr || undefined,
        business_unit: formData.business_unit || undefined,
        matrix_manager: formData.matrix_manager || undefined,
        second_manager: formData.second_manager || undefined,
        custom_manager: formData.custom_manager || undefined,
        review_frequency: formData.review_frequency || undefined,
        custom01: formData.custom01 || undefined,
        custom02: formData.custom02 || undefined,
        custom03: formData.custom03 || undefined,
        custom04: formData.custom04 || undefined,
        custom05: formData.custom05 || undefined,
        custom06: formData.custom06 || undefined,
        custom07: formData.custom07 || undefined,
        custom08: formData.custom08 || undefined,
        custom09: formData.custom09 || undefined,
        custom10: formData.custom10 || undefined,
        custom11: formData.custom11 || undefined,
        custom12: formData.custom12 || undefined,
        custom13: formData.custom13 || undefined,
        custom14: formData.custom14 || undefined,
        custom15: formData.custom15 || undefined,
        login_method: formData.login_method || undefined,
        proxy: formData.proxy || undefined,
        assignment_id_external: formData.assignment_id_external || undefined,
      };

      const response = await createExtendedUser(submitData);
      setSuccess(true);

      // Call success callback after 1 second
      setTimeout(() => {
        if (onSuccess) {
          onSuccess(response);
        }
      }, 1000);

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const renderBasicInformation = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>Basic Information</Typography>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Username"
          value={formData.username}
          onChange={handleChange('username')}
          error={Boolean(errors.username)}
          helperText={errors.username}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          type="email"
          label="Email"
          value={formData.email}
          onChange={handleChange('email')}
          error={Boolean(errors.email)}
          helperText={errors.email}
        />
      </Grid>

      <Grid item xs={12} md={4}>
        <TextField
          required
          fullWidth
          label="First Name"
          value={formData.first_name}
          onChange={handleChange('first_name')}
          error={Boolean(errors.first_name)}
          helperText={errors.first_name}
        />
      </Grid>

      <Grid item xs={12} md={4}>
        <TextField
          required
          fullWidth
          label="Last Name"
          value={formData.last_name}
          onChange={handleChange('last_name')}
          error={Boolean(errors.last_name)}
          helperText={errors.last_name}
        />
      </Grid>

      <Grid item xs={12} md={4}>
        <TextField
          fullWidth
          label="Middle Initial"
          value={formData.middle_initial}
          onChange={handleChange('middle_initial')}
          inputProps={{ maxLength: 1 }}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <FormControl fullWidth required error={Boolean(errors.gender)}>
          <InputLabel>Gender</InputLabel>
          <Select
            value={formData.gender}
            onChange={handleChange('gender')}
            label="Gender"
          >
            <MenuItem value="M">Male</MenuItem>
            <MenuItem value="F">Female</MenuItem>
            <MenuItem value="Other">Other</MenuItem>
            <MenuItem value="Not Specified">Prefer Not to Say</MenuItem>
          </Select>
          {errors.gender && <FormHelperText>{errors.gender}</FormHelperText>}
        </FormControl>
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Employee ID"
          value={formData.employee_id}
          onChange={handleChange('employee_id')}
          error={Boolean(errors.employee_id)}
          helperText={errors.employee_id || 'Unique identifier for the employee'}
        />
      </Grid>

      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Display Name (Optional)"
          value={formData.display_name}
          onChange={handleChange('display_name')}
          helperText="If empty, will use First Name + Last Name"
        />
      </Grid>
    </Grid>
  );

  const renderEmploymentDetails = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>Employment Details</Typography>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Job Title"
          value={formData.title}
          onChange={handleChange('title')}
          error={Boolean(errors.title)}
          helperText={errors.title}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Job Code"
          value={formData.job_code}
          onChange={handleChange('job_code')}
          error={Boolean(errors.job_code)}
          helperText={errors.job_code}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Division"
          value={formData.division}
          onChange={handleChange('division')}
          error={Boolean(errors.division)}
          helperText={errors.division || 'Line of Business'}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Department"
          value={formData.department}
          onChange={handleChange('department')}
          error={Boolean(errors.department)}
          helperText={errors.department}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Work Location"
          value={formData.location}
          onChange={handleChange('location')}
          error={Boolean(errors.location)}
          helperText={errors.location}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label="Hire Date *"
            value={formData.hire_date}
            onChange={handleDateChange('hire_date')}
            renderInput={(params) => (
              <TextField
                {...params}
                fullWidth
                error={Boolean(errors.hire_date)}
                helperText={errors.hire_date}
              />
            )}
          />
        </LocalizationProvider>
      </Grid>

      <Grid item xs={12} md={6}>
        <FormControl fullWidth required>
          <InputLabel>Role</InputLabel>
          <Select
            value={formData.role}
            onChange={handleChange('role')}
            label="Role"
          >
            <MenuItem value="employee">Employee</MenuItem>
            <MenuItem value="hr_manager">HR Manager</MenuItem>
            <MenuItem value="hr_admin">HR Admin</MenuItem>
            <MenuItem value="customer">Customer</MenuItem>
          </Select>
        </FormControl>
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Manager Username"
          value={formData.manager}
          onChange={handleChange('manager')}
          helperText="Username of direct manager or 'NO_MANAGER'"
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="HR Representative"
          value={formData.hr}
          onChange={handleChange('hr')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Business Unit (Optional)"
          value={formData.business_unit}
          onChange={handleChange('business_unit')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Matrix Manager (Optional)"
          value={formData.matrix_manager}
          onChange={handleChange('matrix_manager')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Second Manager (Optional)"
          value={formData.second_manager}
          onChange={handleChange('second_manager')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>Status</InputLabel>
          <Select
            value={formData.status}
            onChange={handleChange('status')}
            label="Status"
          >
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
          </Select>
        </FormControl>
      </Grid>
    </Grid>
  );

  const renderAddressContact = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>Address & Contact Information</Typography>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      <Grid item xs={12}>
        <TextField
          required
          fullWidth
          label="Address Line 1"
          value={formData.address_line1}
          onChange={handleChange('address_line1')}
          error={Boolean(errors.address_line1)}
          helperText={errors.address_line1}
        />
      </Grid>

      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Address Line 2 (Optional)"
          value={formData.address_line2}
          onChange={handleChange('address_line2')}
        />
      </Grid>

      <Grid item xs={12} md={4}>
        <TextField
          required
          fullWidth
          label="City"
          value={formData.city}
          onChange={handleChange('city')}
          error={Boolean(errors.city)}
          helperText={errors.city}
        />
      </Grid>

      <Grid item xs={12} md={4}>
        <TextField
          required
          fullWidth
          label="State"
          value={formData.state}
          onChange={handleChange('state')}
          error={Boolean(errors.state)}
          helperText={errors.state}
        />
      </Grid>

      <Grid item xs={12} md={4}>
        <TextField
          required
          fullWidth
          label="ZIP Code"
          value={formData.zip_code}
          onChange={handleChange('zip_code')}
          error={Boolean(errors.zip_code)}
          helperText={errors.zip_code}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          required
          fullWidth
          label="Country"
          value={formData.country}
          onChange={handleChange('country')}
          error={Boolean(errors.country)}
          helperText={errors.country}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Business Phone (Optional)"
          value={formData.business_phone}
          onChange={handleChange('business_phone')}
          placeholder="(555) 123-4567"
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Business Fax (Optional)"
          value={formData.business_fax}
          onChange={handleChange('business_fax')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>Timezone</InputLabel>
          <Select
            value={formData.timezone}
            onChange={handleChange('timezone')}
            label="Timezone"
          >
            <MenuItem value="US/Pacific">US/Pacific</MenuItem>
            <MenuItem value="US/Mountain">US/Mountain</MenuItem>
            <MenuItem value="US/Central">US/Central</MenuItem>
            <MenuItem value="US/Eastern">US/Eastern</MenuItem>
            <MenuItem value="UTC">UTC</MenuItem>
          </Select>
        </FormControl>
      </Grid>
    </Grid>
  );

  const renderAdditionalDetails = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>Additional Details (Optional)</Typography>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      <Grid item xs={12}>
        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
          Review Information
        </Typography>
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Review Frequency"
          value={formData.review_frequency}
          onChange={handleChange('review_frequency')}
          placeholder="e.g., Annual, Semi-annual"
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label="Last Review Date"
            value={formData.last_review_date}
            onChange={handleDateChange('last_review_date')}
            renderInput={(params) => <TextField {...params} fullWidth />}
          />
        </LocalizationProvider>
      </Grid>

      <Grid item xs={12}>
        <Typography variant="subtitle2" color="textSecondary" gutterBottom sx={{ mt: 2 }}>
          Custom Fields
        </Typography>
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Career Level (Custom01)"
          value={formData.custom01}
          onChange={handleChange('custom01')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Eligibility Flag (Custom02)"
          value={formData.custom02}
          onChange={handleChange('custom02')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="L04 Org Unit (Custom03)"
          value={formData.custom03}
          onChange={handleChange('custom03')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="L05 Org Unit (Custom04)"
          value={formData.custom04}
          onChange={handleChange('custom04')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="EE Subgroup (Custom09)"
          value={formData.custom09}
          onChange={handleChange('custom09')}
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Union (Custom10)"
          value={formData.custom10}
          onChange={handleChange('custom10')}
        />
      </Grid>
    </Grid>
  );

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return renderBasicInformation();
      case 1:
        return renderEmploymentDetails();
      case 2:
        return renderAddressContact();
      case 3:
        return renderAdditionalDetails();
      default:
        return null;
    }
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          Create New User (Extended Profile)
        </Typography>

        <Stepper activeStep={activeStep} sx={{ my: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            User created successfully! Redirecting...
          </Alert>
        )}

        <Box sx={{ mt: 3, mb: 4 }}>
          {renderStepContent(activeStep)}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            disabled={activeStep === 0 || loading}
            onClick={handleBack}
            variant="outlined"
          >
            Back
          </Button>

          <Box sx={{ display: 'flex', gap: 2 }}>
            {onCancel && (
              <Button
                onClick={onCancel}
                disabled={loading}
                variant="outlined"
                color="secondary"
              >
                Cancel
              </Button>
            )}

            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={loading || success}
              >
                {loading ? <CircularProgress size={24} /> : 'Create User'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={loading}
              >
                Next
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ExtendedUserForm;
