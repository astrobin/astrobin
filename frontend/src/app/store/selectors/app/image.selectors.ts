import { AppState } from "@app/store/reducers/app.reducers";
import { selectApp } from "@app/store/selectors/app/app.selectors";
import { createSelector } from "@ngrx/store";
import { ImageInterface } from "@shared/interfaces/image.interface";

export const selectImages = createSelector(selectApp, (state: AppState): ImageInterface[] => state.images);

export const selectImage = createSelector(
  selectImages,
  (images: ImageInterface[], pk: number): ImageInterface => {
    const matching = images.filter(image => image.pk === pk);
    return matching.length > 0 ? matching[0] : null;
  }
);
