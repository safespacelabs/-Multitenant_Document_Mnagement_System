"""
Extended User Management API Router
Handles extended user operations with full profile data
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from datetime import datetime, timedelta
import uuid

from app.schemas import (
    UserCreateExtended,
    UserResponseExtended,
    UserUpdateExtended,
    BulkUserImportResponse,
    UserRole
)
from app.models_company import User
from app.auth import get_current_user
from app.database import get_management_db, get_company_db
from app import models
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["users-extended"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/create-extended", response_model=UserResponseExtended)
async def create_user_extended(
    user_data: UserCreateExtended,
    current_user: User = Depends(get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Create a new user with extended profile information.

    Only accessible by HR Admin or HR Manager.
    All mandatory fields from usertable.csv must be provided.
    """
    # Check permissions
    if current_user.role not in ['hr_admin', 'hr_manager', 'system_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only HR Admin and HR Manager can create users with extended profiles."
        )

    # Get company from management database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    db = next(company_db_gen)

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists"
        )

    # Check if employee_id already exists
    existing_emp = db.query(User).filter(User.employee_id == user_data.employee_id).first()
    if existing_emp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee ID '{user_data.employee_id}' already exists"
        )

    # Create full_name from first_name and last_name for backward compatibility
    full_name = f"{user_data.first_name} {user_data.last_name}".strip()

    # Create S3 folder path
    s3_folder = f"users/{user_data.username}/"

    # Create user with all fields
    new_user = User(
        # Basic fields
        username=user_data.username,
        email=user_data.email.lower(),
        full_name=full_name,
        role=user_data.role.value,
        s3_folder=s3_folder,
        company_id=current_user.company_id,
        created_by=current_user.id,
        password_set=False,
        is_active=True if user_data.status == 'active' else False,

        # Phase 1: Core Identity
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_initial=user_data.middle_initial,
        gender=user_data.gender,
        employee_id=user_data.employee_id,
        status=user_data.status,
        hire_date=user_data.hire_date,
        timezone=user_data.timezone,
        default_locale=user_data.default_locale,
        display_name=user_data.display_name or full_name,

        # Phase 2: Organizational
        manager=user_data.manager,
        division=user_data.division,
        department=user_data.department,
        location=user_data.location,
        job_code=user_data.job_code,
        title=user_data.title,
        hr=user_data.hr,
        business_unit=user_data.business_unit,
        matrix_manager=user_data.matrix_manager,
        second_manager=user_data.second_manager,
        custom_manager=user_data.custom_manager,

        # Phase 3: Address
        address_line1=user_data.address_line1,
        address_line2=user_data.address_line2,
        city=user_data.city,
        state=user_data.state,
        zip_code=user_data.zip_code,
        country=user_data.country,
        business_phone=user_data.business_phone,
        business_fax=user_data.business_fax,

        # Phase 4: Review & Performance
        review_frequency=user_data.review_frequency,
        last_review_date=user_data.last_review_date,
        assignment_uuid=uuid.uuid4(),

        # Phase 5: Custom Fields
        custom01=user_data.custom01,
        custom02=user_data.custom02,
        custom03=user_data.custom03,
        custom04=user_data.custom04,
        custom05=user_data.custom05,
        custom06=user_data.custom06,
        custom07=user_data.custom07,
        custom08=user_data.custom08 or current_user.company_id,
        custom09=user_data.custom09,
        custom10=user_data.custom10,
        custom11=user_data.custom11,
        custom12=user_data.custom12,
        custom13=user_data.custom13,
        custom14=user_data.custom14,
        custom15=user_data.custom15,

        # Phase 6: Auth & Access
        login_method=user_data.login_method,
        proxy=user_data.proxy,
        assignment_id_external=user_data.assignment_id_external,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/{user_id}/extended", response_model=UserResponseExtended)
async def get_user_extended(
    user_id: str,
    current_user: User = Depends(get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Get extended user profile information.

    HR Admin and HR Manager can view any user's extended profile.
    Regular users can only view their own profile.
    """
    # Get company from management database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    db = next(company_db_gen)

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )

    # Check permissions
    if current_user.role not in ['hr_admin', 'hr_manager', 'system_admin']:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own extended profile"
            )

    return user


@router.put("/{user_id}/extended", response_model=UserResponseExtended)
async def update_user_extended(
    user_id: str,
    user_data: UserUpdateExtended,
    current_user: User = Depends(get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Update user with extended profile information.

    HR Admin and HR Manager can update any user.
    Regular users can update their own non-critical fields.
    """
    # Get company from management database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    db = next(company_db_gen)

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )

    # Check permissions
    is_admin = current_user.role in ['hr_admin', 'hr_manager', 'system_admin']
    is_self = current_user.id == user_id

    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    # Update fields
    update_data = user_data.dict(exclude_unset=True)

    # Restricted fields that only admins can update
    admin_only_fields = [
        'role', 'employee_id', 'manager', 'division', 'department',
        'job_code', 'title', 'hire_date', 'status', 'is_active'
    ]

    for field, value in update_data.items():
        # If non-admin tries to update admin-only field
        if not is_admin and field in admin_only_fields:
            continue  # Skip this field

        # Update full_name if first_name or last_name changed
        if field in ['first_name', 'last_name']:
            setattr(user, field, value)
            user.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        else:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.post("/bulk-import", response_model=BulkUserImportResponse)
async def bulk_import_users(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Bulk import users from CSV file matching the usertable.csv schema.

    Only accessible by HR Admin.

    Expected CSV columns (from usertable.csv):
    - USERNAME, EMAIL, FIRSTNAME, LASTNAME, MI, GENDER
    - EMPID, HIREDATE, TITLE, DIVISION, DEPARTMENT, LOCATION, JOBCODE, MANAGER
    - ADDR1, ADDR2, CITY, STATE, ZIP, COUNTRY
    - BIZ_PHONE, FAX, TIMEZONE, DEFAULT_LOCALE, STATUS
    - CUSTOM01-CUSTOM15 (optional)
    """
    # Check permissions
    if current_user.role not in ['hr_admin', 'system_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR Admin can perform bulk user imports"
        )

    # Check file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    # Get company from management database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    db = next(company_db_gen)

    # Read CSV file
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_file)

    imported_users = []
    errors = []

    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # Map job title to system role
            role = map_title_to_role(row.get('TITLE', 'Employee'))

            # Parse hire date
            hire_date_str = row.get('HIREDATE', '')
            hire_date = None
            if hire_date_str:
                try:
                    # Try multiple date formats
                    for date_format in ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']:
                        try:
                            hire_date = datetime.strptime(hire_date_str, date_format).date()
                            break
                        except ValueError:
                            continue
                    if hire_date is None:
                        hire_date = datetime.now().date()
                except:
                    hire_date = datetime.now().date()
            else:
                hire_date = datetime.now().date()

            # Create user data
            user_data = UserCreateExtended(
                username=row['USERNAME'],
                email=row['EMAIL'],
                first_name=row['FIRSTNAME'],
                last_name=row['LASTNAME'],
                middle_initial=row.get('MI'),
                gender=row.get('GENDER', 'Not Specified'),
                employee_id=row['EMPID'],
                hire_date=hire_date,
                title=row['TITLE'],
                division=row.get('DIVISION', 'General Operations'),
                department=row.get('DEPARTMENT', 'General'),
                location=row.get('LOCATION', 'Remote Office'),
                job_code=row.get('JOBCODE', '50000000'),
                manager=row.get('MANAGER', 'NO_MANAGER'),
                address_line1=row.get('ADDR1', 'Address Not Provided'),
                address_line2=row.get('ADDR2'),
                city=row.get('CITY', 'Unknown'),
                state=row.get('STATE', 'CA'),
                zip_code=row.get('ZIP', '00000'),
                country=row.get('COUNTRY', 'United States'),
                business_phone=row.get('BIZ_PHONE'),
                business_fax=row.get('FAX'),
                role=role,
                timezone=row.get('TIMEZONE', 'US/Pacific'),
                default_locale=row.get('DEFAULT_LOCALE', 'en_US'),
                status=row.get('STATUS', 'active'),
                hr=row.get('HR'),
                business_unit=row.get('Business Unit'),
                review_frequency=row.get('REVIEW_FREQ'),
                custom01=row.get('CUSTOM01'),
                custom02=row.get('CUSTOM02'),
                custom03=row.get('CUSTOM03'),
                custom04=row.get('CUSTOM04'),
                custom05=row.get('CUSTOM05'),
                custom06=row.get('CUSTOM06'),
                custom07=row.get('CUSTOM07'),
                custom08=row.get('CUSTOM08'),
                custom09=row.get('CUSTOM09'),
                custom10=row.get('CUSTOM10'),
                custom11=row.get('CUSTOM11'),
                custom12=row.get('CUSTOM12'),
                custom13=row.get('CUSTOM13'),
                custom14=row.get('CUSTOM14'),
                custom15=row.get('CUSTOM15'),
                login_method=row.get('LOGIN_METHOD'),
                assignment_id_external=row.get('ASSIGNMENT_ID_EXTERNAL'),
            )

            # Check if user already exists
            existing = db.query(User).filter(
                (User.username == user_data.username) |
                (User.email == user_data.email) |
                (User.employee_id == user_data.employee_id)
            ).first()

            if existing:
                errors.append(f"Row {row_num}: User already exists (username: {user_data.username}, email: {user_data.email}, or employee_id: {user_data.employee_id})")
                continue

            # Create full_name
            full_name = f"{user_data.first_name} {user_data.last_name}".strip()

            # Create user
            new_user = User(
                username=user_data.username,
                email=user_data.email.lower(),
                full_name=full_name,
                role=user_data.role.value,
                s3_folder=f"users/{user_data.username}/",
                company_id=current_user.company_id,
                created_by=current_user.id,
                password_set=False,
                is_active=True if user_data.status == 'active' else False,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                middle_initial=user_data.middle_initial,
                gender=user_data.gender,
                employee_id=user_data.employee_id,
                status=user_data.status,
                hire_date=user_data.hire_date,
                timezone=user_data.timezone,
                default_locale=user_data.default_locale,
                display_name=user_data.display_name or full_name,
                manager=user_data.manager,
                division=user_data.division,
                department=user_data.department,
                location=user_data.location,
                job_code=user_data.job_code,
                title=user_data.title,
                hr=user_data.hr,
                business_unit=user_data.business_unit,
                address_line1=user_data.address_line1,
                address_line2=user_data.address_line2,
                city=user_data.city,
                state=user_data.state,
                zip_code=user_data.zip_code,
                country=user_data.country,
                business_phone=user_data.business_phone,
                business_fax=user_data.business_fax,
                review_frequency=user_data.review_frequency,
                assignment_uuid=uuid.uuid4(),
                custom01=user_data.custom01,
                custom02=user_data.custom02,
                custom03=user_data.custom03,
                custom04=user_data.custom04,
                custom05=user_data.custom05,
                custom06=user_data.custom06,
                custom07=user_data.custom07,
                custom08=user_data.custom08 or current_user.company_id,
                custom09=user_data.custom09,
                custom10=user_data.custom10,
                custom11=user_data.custom11,
                custom12=user_data.custom12,
                custom13=user_data.custom13,
                custom14=user_data.custom14,
                custom15=user_data.custom15,
                login_method=user_data.login_method,
                assignment_id_external=user_data.assignment_id_external,
            )

            db.add(new_user)
            imported_users.append(user_data.username)

        except KeyError as e:
            errors.append(f"Row {row_num}: Missing required column: {str(e)}")
        except ValueError as e:
            errors.append(f"Row {row_num}: Invalid value: {str(e)}")
        except Exception as e:
            errors.append(f"Row {row_num}: Error: {str(e)}")

    # Commit all successful imports
    if imported_users:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save users to database: {str(e)}"
            )

    return BulkUserImportResponse(
        imported_count=len(imported_users),
        imported_users=imported_users,
        errors=errors
    )


@router.get("/extended/list", response_model=List[UserResponseExtended])
async def list_users_extended(
    skip: int = 0,
    limit: int = 100,
    department: str = None,
    division: str = None,
    status: str = None,
    current_user: User = Depends(get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """
    List all users with extended profile information.

    Supports filtering by department, division, and status.
    Only accessible by HR Admin and HR Manager.
    """
    # Check permissions
    if current_user.role not in ['hr_admin', 'hr_manager', 'system_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR Admin and HR Manager can list all users"
        )

    # Get company from management database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    db = next(company_db_gen)

    # Build query
    query = db.query(User)

    if department:
        query = query.filter(User.department == department)

    if division:
        query = query.filter(User.division == division)

    if status:
        query = query.filter(User.status == status)

    # Execute query
    users = query.offset(skip).limit(limit).all()

    return users


def map_title_to_role(title: str) -> UserRole:
    """Map job title to system role"""
    title_lower = title.lower()

    if 'hr' in title_lower and 'admin' in title_lower:
        return UserRole.hr_admin
    elif 'hr' in title_lower or 'manager' in title_lower:
        return UserRole.hr_manager
    elif 'customer' in title_lower or 'client' in title_lower:
        return UserRole.customer
    else:
        return UserRole.employee
