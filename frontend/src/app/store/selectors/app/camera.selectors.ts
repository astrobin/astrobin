import { AppState } from "@app/store/reducers/app.reducers";
import { selectApp } from "@app/store/selectors/app/app.selectors";
import { createSelector } from "@ngrx/store";
import { CameraInterface } from "@shared/interfaces/camera.interface";

export const selectCameras = createSelector(selectApp, (state: AppState): CameraInterface[] => state.cameras);

export const selectCamera = createSelector(
  selectCameras,
  (cameras: CameraInterface[], pk: number): CameraInterface => {
    const matching = cameras.filter(camera => camera.pk === pk);
    return matching.length > 0 ? matching[0] : null;
  }
);
