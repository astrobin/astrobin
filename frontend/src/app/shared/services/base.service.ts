import { Injectable, OnDestroy } from "@angular/core";
import { LoadingService } from "@shared/services/loading.service";
import { Observable, Subject } from "rxjs";
import { debounceTime } from "rxjs/operators";

@Injectable()
export class BaseService implements OnDestroy {
  destroyedSubject = new Subject<void>();
  destroyed$ = this.destroyedSubject.asObservable();

  loadingSubject = new Subject<boolean>();
  loading$: Observable<boolean> = this.loadingSubject.asObservable().pipe(debounceTime(LoadingService.DEBOUNCE_TIME));

  constructor(public loadingService: LoadingService) {
    this.loading$.subscribe(value => this.loadingService.setLoading(value));
  }

  ngOnDestroy(): void {
    this.destroyedSubject.next();
  }
}
