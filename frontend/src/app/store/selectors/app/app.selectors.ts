import { AppState } from "@app/store/reducers/app.reducers";
import { State } from "@app/store/state";
import { createSelector } from "@ngrx/store";
import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";

export const selectApp = (state: State): AppState => state.app;

export const selectBreadcrumb = createSelector(selectApp, state => state.breadcrumb);

export const selectBackendConfig = createSelector(selectApp, (state): BackendConfigInterface => state.backendConfig);

export const selectIotdMaxSubmissionsPerDay = createSelector(
  selectBackendConfig,
  (backendConfig): number => backendConfig.IOTD_SUBMISSION_MAX_PER_DAY
);

export const selectIotdMaxReviewsPerDay = createSelector(
  selectBackendConfig,
  (backendConfig): number => backendConfig.IOTD_REVIEW_MAX_PER_DAY
);
