import { Injectable } from "@angular/core";
import { LoadImages } from "@app/store/actions/image.actions";
import { LoadSolutions } from "@app/store/actions/solution.actions";
import { selectBackendConfig } from "@app/store/selectors/app/app.selectors";
import { selectImages } from "@app/store/selectors/app/image.selectors";
import { selectSolutions } from "@app/store/selectors/app/solution.selectors";
import { State } from "@app/store/state";
import { IotdApiService } from "@features/iotd/services/iotd-api.service";
import { Actions, Effect, ofType } from "@ngrx/effects";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { LoadingService } from "@shared/services/loading.service";
import { PopNotificationsService } from "@shared/services/pop-notifications.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { of } from "rxjs";
import { catchError, map, mergeMap, skip, switchMap, take, tap } from "rxjs/operators";
import {
  DeleteSubmissionFailure,
  DeleteSubmissionSuccess,
  DeleteVoteFailure,
  DeleteVoteSuccess,
  DismissImageSuccess,
  HideImageSuccess,
  IotdActions,
  IotdActionTypes,
  LoadDismissedImagesSuccess,
  LoadHiddenImagesSuccess,
  LoadReviewQueueFailure,
  LoadReviewQueueSuccess,
  LoadSubmissionQueueFailure,
  LoadSubmissionQueueSuccess,
  LoadSubmissionsFailure,
  LoadSubmissionsSuccess,
  LoadVotesFailure,
  LoadVotesSuccess,
  PostSubmissionFailure,
  PostSubmissionSuccess,
  PostVoteFailure,
  PostVoteSuccess,
  ShowImageSuccess
} from "./iotd.actions";

@Injectable()
export class IotdEffects {
  @Effect()
  loadSubmissionQueue$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_SUBMISSION_QUEUE),
    tap(() => this.loadingService.setLoading(true)),
    mergeMap(action =>
      this.iotdApiService.getSubmissionQueueEntries(action.payload.page).pipe(
        tap(entries => this.store$.dispatch(new LoadImages(entries.results.map(entry => entry.pk)))),
        switchMap(entries =>
          this.store$.select(selectBackendConfig).pipe(
            map(backendConfig => ({
              entries,
              contentTypeId: backendConfig.IMAGE_CONTENT_TYPE_ID
            }))
          )
        ),
        switchMap(({ entries, contentTypeId }) =>
          this.store$.select(selectImages).pipe(
            skip(1),
            take(1),
            map(() => ({ entries, contentTypeId }))
          )
        ),
        tap(({ entries, contentTypeId }) =>
          this.store$.dispatch(
            new LoadSolutions({ contentType: contentTypeId, objectIds: entries.results.map(entry => "" + entry.pk) })
          )
        ),
        switchMap(({ entries, contentTypeId }) =>
          this.store$.select(selectSolutions).pipe(
            skip(1),
            take(1),
            map(() => entries)
          )
        ),
        map(entries => new LoadSubmissionQueueSuccess(entries)),
        catchError(error => of(new LoadSubmissionQueueFailure()))
      )
    )
  );

  @Effect({ dispatch: false })
  loadSubmissionQueueSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_SUBMISSION_QUEUE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  loadSubmissionQueueFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_SUBMISSION_QUEUE_FAILURE),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  loadSubmissions$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_SUBMISSIONS),
    tap(() => this.loadingService.setLoading(true)),
    mergeMap(action =>
      this.iotdApiService.getSubmissions().pipe(
        map(submissions => new LoadSubmissionsSuccess(submissions)),
        catchError(error => of(new LoadSubmissionsFailure()))
      )
    )
  );

  @Effect({ dispatch: false })
  loadSubmissionsSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_SUBMISSIONS_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  loadSubmissionsFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_SUBMISSIONS_FAILURE),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  postSubmission$ = this.actions$.pipe(
    ofType(IotdActionTypes.POST_SUBMISSION),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService.addSubmission(payload.imageId).pipe(
        map(response => new PostSubmissionSuccess(response)),
        catchError(error => of(new PostSubmissionFailure(error)))
      )
    )
  );

  @Effect({ dispatch: false })
  postSubmissionSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.POST_SUBMISSION_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  postSubmissionFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.POST_SUBMISSION_FAILURE),
    map(action => action.payload.error),
    tap(error => {
      this.popNotificationsService.error(error);
      this.loadingService.setLoading(false);
    })
  );

  @Effect()
  deleteSubmission$ = this.actions$.pipe(
    ofType(IotdActionTypes.DELETE_SUBMISSION),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService.retractSubmission(payload.id).pipe(
        map(() => new DeleteSubmissionSuccess({ id: payload.id })),
        catchError(error => of(new DeleteSubmissionFailure()))
      )
    )
  );

  @Effect({ dispatch: false })
  deleteSubmissionSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.DELETE_SUBMISSION_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  deleteSubmissionFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.DELETE_SUBMISSION_FAILURE),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  loadHiddenImage$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_HIDDEN_IMAGES),
    tap(() => this.loadingService.setLoading(true)),
    mergeMap(() =>
      this.iotdApiService.loadHiddenImages().pipe(map(hiddenImages => new LoadHiddenImagesSuccess({ hiddenImages })))
    )
  );

  @Effect({ dispatch: false })
  loadHiddenImagesSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_HIDDEN_IMAGES_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  hideImage$ = this.actions$.pipe(
    ofType(IotdActionTypes.HIDE_IMAGE),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService.hideImage(payload.id).pipe(map(hiddenImage => new HideImageSuccess({ hiddenImage })))
    )
  );

  @Effect({ dispatch: false })
  hideImageSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.HIDE_IMAGE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  showImage$ = this.actions$.pipe(
    ofType(IotdActionTypes.SHOW_IMAGE),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService.showImage(payload.hiddenImage).pipe(map(id => new ShowImageSuccess({ id })))
    )
  );

  @Effect({ dispatch: false })
  showImageSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.SHOW_IMAGE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  loadDismissedImage$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_DISMISSED_IMAGES),
    tap(() => this.loadingService.setLoading(true)),
    mergeMap(() =>
      this.iotdApiService
        .loadDismissedImages()
        .pipe(map(dismissedImages => new LoadDismissedImagesSuccess({ dismissedImages })))
    )
  );

  @Effect({ dispatch: false })
  loadDismissedImagesSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_DISMISSED_IMAGES_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  dismissImage$ = this.actions$.pipe(
    ofType(IotdActionTypes.DISMISS_IMAGE),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService
        .dismissImage(payload.id)
        .pipe(map(dismissedImage => new DismissImageSuccess({ dismissedImage })))
    )
  );

  @Effect({ dispatch: false })
  dismissImageSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.DISMISS_IMAGE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  loadReviewQueue$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_REVIEW_QUEUE),
    tap(() => this.loadingService.setLoading(true)),
    mergeMap(action =>
      this.iotdApiService.getReviewQueueEntries(action.payload.page).pipe(
        tap(entries => this.store$.dispatch(new LoadImages(entries.results.map(entry => entry.pk)))),
        switchMap(entries =>
          this.store$.select(selectBackendConfig).pipe(
            map(backendConfig => ({
              entries,
              contentTypeId: backendConfig.IMAGE_CONTENT_TYPE_ID
            }))
          )
        ),
        switchMap(({ entries, contentTypeId }) =>
          this.store$.select(selectImages).pipe(
            skip(1),
            take(1),
            map(() => ({ entries, contentTypeId }))
          )
        ),
        tap(({ entries, contentTypeId }) =>
          this.store$.dispatch(
            new LoadSolutions({ contentType: contentTypeId, objectIds: entries.results.map(entry => "" + entry.pk) })
          )
        ),
        switchMap(({ entries, contentTypeId }) =>
          this.store$.select(selectSolutions).pipe(
            skip(1),
            take(1),
            map(() => entries)
          )
        ),
        map(entries => new LoadReviewQueueSuccess(entries)),
        catchError(() => of(new LoadReviewQueueFailure()))
      )
    )
  );

  @Effect({ dispatch: false })
  loadReviewQueueSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_REVIEW_QUEUE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  loadReviewQueueFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_REVIEW_QUEUE_FAILURE),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  loadVotes$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_VOTES),
    tap(() => this.loadingService.setLoading(true)),
    mergeMap(action =>
      this.iotdApiService.getVotes().pipe(
        map(reviews => new LoadVotesSuccess(reviews)),
        catchError(error => of(new LoadVotesFailure()))
      )
    )
  );

  @Effect({ dispatch: false })
  loadVotesSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_VOTES_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  loadVotesFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.LOAD_VOTES_FAILURE),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect()
  postVote$ = this.actions$.pipe(
    ofType(IotdActionTypes.POST_VOTE),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService.addVote(payload.imageId).pipe(
        map(response => new PostVoteSuccess(response)),
        catchError(error => of(new PostVoteFailure(error)))
      )
    )
  );

  @Effect({ dispatch: false })
  postVoteSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.POST_VOTE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  postVoteFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.POST_VOTE_FAILURE),
    map(action => action.payload.error),
    tap(error => {
      this.popNotificationsService.error(error);
      this.loadingService.setLoading(false);
    })
  );

  @Effect()
  deleteVote$ = this.actions$.pipe(
    ofType(IotdActionTypes.DELETE_VOTE),
    tap(() => this.loadingService.setLoading(true)),
    map(action => action.payload),
    mergeMap(payload =>
      this.iotdApiService.retractVote(payload.id).pipe(
        map(() => new DeleteVoteSuccess({ id: payload.id })),
        catchError(() => of(new DeleteVoteFailure()))
      )
    )
  );

  @Effect({ dispatch: false })
  deleteVoteSuccess$ = this.actions$.pipe(
    ofType(IotdActionTypes.DELETE_VOTE_SUCCESS),
    tap(() => this.loadingService.setLoading(false))
  );

  @Effect({ dispatch: false })
  deleteVoteFailure$ = this.actions$.pipe(
    ofType(IotdActionTypes.DELETE_VOTE_FAILURE),
    tap(() => this.loadingService.setLoading(false))
  );

  constructor(
    public readonly store$: Store<State>,
    public readonly actions$: Actions<IotdActions>,
    public readonly iotdApiService: IotdApiService,
    public readonly loadingService: LoadingService,
    public readonly popNotificationsService: PopNotificationsService,
    public readonly translateService: TranslateService,
    public readonly windowRef: WindowRefService
  ) {}
}
