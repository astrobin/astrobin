import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { ReviewImageInterface, SubmissionImageInterface } from "@features/iotd/store/iotd.reducer";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

export interface SubmissionInterface {
  id: number;
  submitter: number;
  image: number;
  date: string;
}

export interface VoteInterface {
  id: number;
  reviewer: number;
  image: number;
  date: string;
}

export interface HiddenImage {
  id: number;
  user: number;
  image: number;
  created: string;
}

export interface DismissedImage {
  id: number;
  user: number;
  image: number;
  created: string;
}

@Injectable()
export class IotdApiService extends BaseClassicApiService {
  constructor(public readonly loadingService: LoadingService, public readonly http: HttpClient) {
    super(loadingService);
  }

  getSubmissionQueueEntries(page = 1): Observable<PaginatedApiResultInterface<SubmissionImageInterface>> {
    return this.http.get<PaginatedApiResultInterface<SubmissionImageInterface>>(
      `${this.baseUrl}/iotd/submission-queue/?page=${page}`
    );
  }

  getSubmissions(): Observable<SubmissionInterface[]> {
    return this.http.get<SubmissionInterface[]>(`${this.baseUrl}/iotd/submission/`);
  }

  addSubmission(imageId: number): Observable<SubmissionInterface> {
    return this.http.post<SubmissionInterface>(`${this.baseUrl}/iotd/submission/`, { image: imageId });
  }

  retractSubmission(id: number): Observable<SubmissionInterface> {
    return this.http.delete<SubmissionInterface>(`${this.baseUrl}/iotd/submission/${id}/`);
  }

  getReviewQueueEntries(page = 1): Observable<PaginatedApiResultInterface<ReviewImageInterface>> {
    return this.http.get<PaginatedApiResultInterface<ReviewImageInterface>>(
      `${this.baseUrl}/iotd/review-queue/?page=${page}`
    );
  }

  getVotes(): Observable<VoteInterface[]> {
    return this.http.get<VoteInterface[]>(`${this.baseUrl}/iotd/vote/`);
  }

  addVote(imageId: number): Observable<VoteInterface> {
    return this.http.post<VoteInterface>(`${this.baseUrl}/iotd/vote/`, { image: imageId });
  }

  retractVote(id: number): Observable<VoteInterface> {
    return this.http.delete<VoteInterface>(`${this.baseUrl}/iotd/vote/${id}/`);
  }

  loadHiddenImages(): Observable<HiddenImage[]> {
    return this.http.get<HiddenImage[]>(`${this.baseUrl}/iotd/hidden-image/`);
  }

  hideImage(id: number): Observable<HiddenImage> {
    return this.http.post<HiddenImage>(`${this.baseUrl}/iotd/hidden-image/`, { image: id });
  }

  showImage(hiddenImage: HiddenImage): Observable<number> {
    return this.http
      .delete<void>(`${this.baseUrl}/iotd/hidden-image/${hiddenImage.id}/`)
      .pipe(map(() => hiddenImage.image));
  }

  loadDismissedImages(): Observable<DismissedImage[]> {
    return this.http.get<DismissedImage[]>(`${this.baseUrl}/iotd/dismissed-image/`);
  }

  dismissImage(id: number): Observable<DismissedImage> {
    return this.http.post<DismissedImage>(`${this.baseUrl}/iotd/dismissed-image/`, { image: id });
  }
}
