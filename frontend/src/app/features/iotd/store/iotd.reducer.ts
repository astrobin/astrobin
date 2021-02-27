import {
  DismissedImage,
  HiddenImage,
  SubmissionInterface,
  VoteInterface
} from "@features/iotd/services/iotd-api.service";
import { ImageInterface } from "@shared/interfaces/image.interface";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { IotdActions, IotdActionTypes } from "./iotd.actions";

export const iotdFeatureKey = "iotd";

// tslint:disable-next-line:no-empty-interface
export interface SubmissionImageInterface extends ImageInterface {}

// tslint:disable-next-line:no-empty-interface
export interface ReviewImageInterface extends ImageInterface {}

export type PromotionImageInterface = SubmissionImageInterface | ReviewImageInterface;

export interface IotdState {
  submissionQueue: PaginatedApiResultInterface<SubmissionImageInterface> | null;
  submissions: SubmissionInterface[];

  reviewQueue: PaginatedApiResultInterface<ReviewImageInterface> | null;
  votes: VoteInterface[];

  hiddenImages: HiddenImage[];
  dismissedImages: DismissedImage[];
  dismissConfirmationSeen: boolean;
}

export const initialIotdState: IotdState = {
  submissionQueue: null,
  submissions: [],

  reviewQueue: null,
  votes: [],

  hiddenImages: [],
  dismissedImages: [],
  dismissConfirmationSeen: false
};

export function reducer(state = initialIotdState, action: IotdActions): IotdState {
  switch (action.type) {
    case IotdActionTypes.LOAD_SUBMISSION_QUEUE_SUCCESS:
      return {
        ...state,
        submissionQueue: action.payload
      };

    case IotdActionTypes.LOAD_SUBMISSIONS_SUCCESS:
      return {
        ...state,
        submissions: action.payload
      };

    case IotdActionTypes.POST_SUBMISSION_SUCCESS:
      return {
        ...state,
        submissions: [...state.submissions, ...[action.payload]]
      };

    case IotdActionTypes.DELETE_SUBMISSION_SUCCESS:
      return {
        ...state,
        submissions: state.submissions.filter(submission => submission.id !== action.payload.id)
      };

    case IotdActionTypes.LOAD_HIDDEN_IMAGES_SUCCESS:
      return {
        ...state,
        hiddenImages: action.payload.hiddenImages
      };

    case IotdActionTypes.HIDE_IMAGE_SUCCESS:
      return {
        ...state,
        hiddenImages: [...state.hiddenImages, action.payload.hiddenImage]
      };

    case IotdActionTypes.LOAD_DISMISSED_IMAGES_SUCCESS:
      return {
        ...state,
        dismissedImages: action.payload.dismissedImages
      };

    case IotdActionTypes.DISMISS_IMAGE_SUCCESS:
      return {
        ...state,
        dismissedImages: [...state.dismissedImages, action.payload.dismissedImage]
      };

    case IotdActionTypes.DISMISS_CONFIRMATION_SEEN:
      return {
        ...state,
        dismissConfirmationSeen: true
      };

    case IotdActionTypes.SHOW_IMAGE_SUCCESS:
      return {
        ...state,
        hiddenImages: state.hiddenImages.filter(hiddenImage => hiddenImage.image !== action.payload.id)
      };

    case IotdActionTypes.LOAD_REVIEW_QUEUE_SUCCESS:
      return {
        ...state,
        reviewQueue: action.payload
      };

    case IotdActionTypes.LOAD_VOTES_SUCCESS:
      return {
        ...state,
        votes: action.payload
      };

    case IotdActionTypes.POST_VOTE_SUCCESS:
      return {
        ...state,
        votes: [...state.votes, ...[action.payload]]
      };

    case IotdActionTypes.DELETE_VOTE_SUCCESS:
      return {
        ...state,
        votes: state.votes.filter(review => review.id !== action.payload.id)
      };

    default:
      return state;
  }
}
