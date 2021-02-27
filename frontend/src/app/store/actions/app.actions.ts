// tslint:disable:max-classes-per-file

import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { LoadCamera, LoadCameraSuccess } from "@app/store/actions/camera.actions";
import { LoadContentType, LoadContentTypeSuccess } from "@app/store/actions/content-type.actions";
import { HideFullscreenImage, ShowFullscreenImage } from "@app/store/actions/fullscreen-image.actions";
import { LoadImage, LoadImages, LoadImagesSuccess, LoadImageSuccess } from "@app/store/actions/image.actions";
import { InitializeApp, InitializeAppSuccess } from "@app/store/actions/initialize-app.actions";
import {
  LoadSolution,
  LoadSolutions,
  LoadSolutionsSuccess,
  LoadSolutionSuccess
} from "@app/store/actions/solution.actions";
import { LoadTelescope, LoadTelescopeSuccess } from "@app/store/actions/telescope.actions";
import { LoadThumbnail, LoadThumbnailSuccess } from "@app/store/actions/thumbnail.actions";

export enum AppActionTypes {
  INITIALIZE = "[App] Initialize",
  INITIALIZE_SUCCESS = "[App] Initialize success",

  SET_BREADCRUMB = "[App] Set breadcrumb",

  SHOW_FULLSCREEN_IMAGE = "[App] Show full screen image",
  HIDE_FULLSCREEN_IMAGE = "[App] Hide full screen image",

  LOAD_CONTENT_TYPE = "[App] Load content type",
  LOAD_CONTENT_TYPE_SUCCESS = "[App] Load content type success",

  LOAD_IMAGE = "[App] Load image",
  LOAD_IMAGE_SUCCESS = "[App] Load image success",

  LOAD_IMAGES = "[App] Load images",
  LOAD_IMAGES_SUCCESS = "[App] Load images success",

  LOAD_THUMBNAIL = "[App] Load thumbnail",
  LOAD_THUMBNAIL_SUCCESS = "[App] Load thumbnail success",

  LOAD_SOLUTION = "[App] Load solution",
  LOAD_SOLUTION_SUCCESS = "[App] Load solution success",

  LOAD_SOLUTIONS = "[App] Load solutions",
  LOAD_SOLUTIONS_SUCCESS = "[App] Load solutions success",

  LOAD_TELESCOPE = "[App] Load telescope",
  LOAD_TELESCOPE_SUCCESS = "[App] Load telescope success",

  LOAD_CAMERA = "[App] Load camera",
  LOAD_CAMERA_SUCCESS = "[App] Load camera success"
}

export type All =
  | InitializeApp
  | InitializeAppSuccess
  | SetBreadcrumb
  | ShowFullscreenImage
  | HideFullscreenImage
  | LoadContentType
  | LoadContentTypeSuccess
  | LoadImage
  | LoadImageSuccess
  | LoadImages
  | LoadImagesSuccess
  | LoadThumbnail
  | LoadThumbnailSuccess
  | LoadSolution
  | LoadSolutionSuccess
  | LoadSolutions
  | LoadSolutionsSuccess
  | LoadTelescope
  | LoadTelescopeSuccess
  | LoadCamera
  | LoadCameraSuccess;
