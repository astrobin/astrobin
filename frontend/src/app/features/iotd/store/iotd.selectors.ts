import {
  DismissedImage,
  HiddenImage,
  SubmissionInterface,
  VoteInterface
} from "@features/iotd/services/iotd-api.service";
import { createFeatureSelector, createSelector } from "@ngrx/store";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import * as fromIotd from "./iotd.reducer";
import { IotdState, ReviewImageInterface, SubmissionImageInterface } from "./iotd.reducer";

export const selectIotdState = createFeatureSelector<fromIotd.IotdState>(fromIotd.iotdFeatureKey);

export const selectSubmissionQueue = createSelector(
  selectIotdState,
  (state: IotdState): PaginatedApiResultInterface<SubmissionImageInterface> => state.submissionQueue
);

export const selectSubmissions = createSelector(
  selectIotdState,
  (state: IotdState): SubmissionInterface[] => state.submissions
);

export const selectSubmissionForImage = createSelector(
  selectSubmissions,
  (submissions: SubmissionInterface[], imageId: number): SubmissionInterface => {
    const matching = submissions.filter(submission => submission.image === imageId);
    if (matching.length === 1) {
      return matching[0];
    }

    return null;
  }
);

export const selectReviewQueue = createSelector(
  selectIotdState,
  (state: IotdState): PaginatedApiResultInterface<ReviewImageInterface> => state.reviewQueue
);

export const selectReviews = createSelector(selectIotdState, (state: IotdState): VoteInterface[] => state.votes);

export const selectReviewForImage = createSelector(
  selectReviews,
  (reviews: VoteInterface[], imageId: number): VoteInterface => {
    const matching = reviews.filter(review => review.image === imageId);
    if (matching.length === 1) {
      return matching[0];
    }

    return null;
  }
);

export const selectHiddenImages = createSelector(
  selectIotdState,
  (state: IotdState): HiddenImage[] => state.hiddenImages
);

export const selectHiddenImageByImageId = createSelector(
  selectHiddenImages,
  (hiddenImages: HiddenImage[], imageId: number): HiddenImage => {
    const matching = hiddenImages.filter(hiddenImage => hiddenImage.image === imageId);
    if (matching.length === 1) {
      return matching[0];
    }

    return null;
  }
);

export const selectDismissedImages = createSelector(
  selectIotdState,
  (state: IotdState): DismissedImage[] => state.dismissedImages
);

export const selectDismissedImageByImageId = createSelector(
  selectDismissedImages,
  (dismissedImages: DismissedImage[], imageId: number): DismissedImage => {
    const matching = dismissedImages.filter(dismissedImage => dismissedImage.image === imageId);
    if (matching.length === 1) {
      return matching[0];
    }

    return null;
  }
);

export const selectDismissConfirmationSeen = createSelector(
  selectIotdState,
  (state: IotdState): boolean => state.dismissConfirmationSeen
);
