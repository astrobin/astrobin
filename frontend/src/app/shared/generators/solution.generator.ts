import { SolutionInterface, SolutionStatus } from "@shared/interfaces/solution.interface";

export class SolutionGenerator {
  static solution(source: Partial<SolutionInterface> = {}): SolutionInterface {
    return {
      id: source.id || 1,
      status: SolutionStatus.ADVANCED_SUCCESS,
      submission_id: 1,
      object_id: "1",
      image_file: null,
      skyplot_zoom1: null,
      objects_in_field: "",
      ra: null,
      dec: null,
      pixscale: null,
      orientation: null,
      radius: null,
      annotations: "",
      pixinsight_serial_number: null,
      pixinsight_svg_annotation_hd: null,
      pixinsight_svg_annotation_regular: null,
      advanced_ra: null,
      advanced_ra_top_left: null,
      advanced_ra_top_right: null,
      advanced_ra_bottom_left: null,
      advanced_ra_bottom_right: null,
      advanced_dec: null,
      advanced_dec_top_left: null,
      advanced_dec_top_right: null,
      advanced_dec_bottom_left: null,
      advanced_dec_bottom_right: null,
      advanced_pixscale: null,
      advanced_orientation: null,
      advanced_flipped: null,
      advanced_wcs_transformation: null,
      advanced_matrix_rect: null,
      advanced_matrix_delta: null,
      advanced_ra_matrix: "",
      advanced_dec_matrix: "",
      advanced_annotations: "",
      advanced_annotations_regular: "",
      settings: 1,
      content_type: 1,
      advanced_settings: 1
    };
  }
}
