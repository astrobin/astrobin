export enum SolutionStatus {
  MISSING = 0,
  PENDING = 1,
  FAILED = 2,
  SUCCESS = 3,
  ADVANCED_PENDING = 4,
  ADVANCED_FAILED = 5,
  ADVANCED_SUCCESS = 6
}

export interface SolutionInterface {
  id: number;
  status: SolutionStatus;
  submission_id: number;
  object_id: string;
  image_file: string;
  skyplot_zoom1: string;
  objects_in_field: string;
  ra: string;
  dec: string;
  pixscale: string;
  orientation: string;
  radius: string;
  annotations: string;
  pixinsight_serial_number: string;
  pixinsight_svg_annotation_hd: string;
  pixinsight_svg_annotation_regular: string;
  advanced_ra: string;
  advanced_ra_top_left: string;
  advanced_ra_top_right: string;
  advanced_ra_bottom_left: string;
  advanced_ra_bottom_right: string;
  advanced_dec: string;
  advanced_dec_top_left: string;
  advanced_dec_top_right: string;
  advanced_dec_bottom_left: string;
  advanced_dec_bottom_right: string;
  advanced_pixscale: string;
  advanced_orientation: string;
  advanced_flipped: boolean;
  advanced_wcs_transformation: string;
  advanced_matrix_rect: string;
  advanced_matrix_delta: string;
  advanced_ra_matrix: string;
  advanced_dec_matrix: string;
  advanced_annotations: string;
  advanced_annotations_regular: string;
  settings: number;
  content_type: number;
  advanced_settings: number;
}
