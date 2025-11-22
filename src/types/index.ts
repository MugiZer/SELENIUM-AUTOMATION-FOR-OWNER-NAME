export interface PropertyData {
  civic_number: string;
  street_name: string;
  postal_code: string;
  owner_names?: string;
  owner_type?: string;
  matricule?: string;
  tax_account_number?: string;
  municipality?: string;
  fiscal_years?: string;
  nb_logements?: string;
  assessed_terrain_current?: string;
  assessed_batiment_current?: string;
  assessed_total_current?: string;
  assessed_total_previous?: string;
  tax_distribution_json?: string;
  last_fetched_at?: string;
  source_url?: string;
  status?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface UploadResponse {
  filename: string;
  path: string;
  totalRecords: number;
  processedRecords: number;
  errors: string[];
}
