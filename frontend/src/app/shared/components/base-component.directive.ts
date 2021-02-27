import { Directive, OnDestroy } from "@angular/core";
import { Subject } from "rxjs";

@Directive()
export class BaseComponentDirective implements OnDestroy {
  destroyedSubject = new Subject();
  destroyed$ = this.destroyedSubject.asObservable();

  ngOnDestroy(): void {
    this.destroyedSubject.next();
  }
}
