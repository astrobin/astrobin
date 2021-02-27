import { AppState } from "@app/store/reducers/app.reducers";
import { selectApp } from "@app/store/selectors/app/app.selectors";
import { createSelector } from "@ngrx/store";
import { ContentTypeInterface } from "@shared/interfaces/content-type.interface";

export const selectContentTypes = createSelector(
  selectApp,
  (state: AppState): ContentTypeInterface[] => state.contentTypes
);

export const selectContentType = createSelector(
  selectContentTypes,
  (contentTypes: ContentTypeInterface[], data: { appLabel: string; model: string }): ContentTypeInterface => {
    const matching = contentTypes.filter(
      contentType => !!contentType && contentType.appLabel === data.appLabel && contentType.model === data.model
    );
    return matching.length > 0 ? matching[0] : null;
  }
);
