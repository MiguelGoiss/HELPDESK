# Modelos de Colaboradores
from .employees import Employees
from .companies import Companies
from .employees_companies import EmployeesCompanies
from .employee_logs import EmployeeLogs
from .departments import Departments
from .locals import Locals
from .employee_contacts import EmployeeContacts
from .employee_contact_types import EmployeeContactTypes
from .employee_employee_permissions import Employee_EmployeePermissions
from .employee_permissions import EmployeePermissions

# Modelos de Tickets
from .tickets import Tickets
from .ticket_types import TicketTypes
from .ticket_suppliers import TicketSuppliers
from .ticket_supplier_contacts import TicketSupplierContacts
from .ticket_subcategories import TicketSubcategories
from .ticket_statuses import TicketStatuses
from .ticket_priorities import TicketPriorities
from .ticket_presets import TicketPresets
from .ticket_logs import TicketLogs
from .ticket_equipments import TicketEquipments
from .ticket_categories import TicketCategories
from .ticket_categories_companies import TicketCategories_Companies
from .ticket_attachments import TicketAttachments
from .ticket_assistance_types import TicketAssistanceTypes
from .tickets_ccs import Tickets_CCS


__tickets__ = [
  "Tickets",
  "TicketLogs",
  "TicketAttachments",
  "Employees",
  "TicketPresets"
]

__all__ = [
  "Employees",
  "Companies",
  "EmployeesCompanies",
  "EmployeeLogs",
  "Departments",
  "Locals",
  "EmployeeContacts",
  "EmployeeContactTypes",
  "Employee_EmployeePermissions",
  "EmployeePermissions",
  "Tickets",
  "TicketTypes",
  "TicketSuppliers",
  "TicketSupplierContacts",
  "TicketSubcategories",
  "TicketStatuses",
  "TicketPriorities",
  "TicketPresets",
  "TicketLogs",
  "TicketEquipments",
  "TicketCategories",
  "TicketCategories_Companies",
  "TicketAttachments",
  "TicketAssistanceTypes",
  "Tickets_CCS"
]
