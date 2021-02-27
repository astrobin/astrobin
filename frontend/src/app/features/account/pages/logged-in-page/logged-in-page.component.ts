import { Component, OnInit } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { interval } from "rxjs";
import { take, tap } from "rxjs/operators";

@Component({
  selector: "astrobin-logged-in-page",
  templateUrl: "./logged-in-page.component.html"
})
export class LoggedInPageComponent extends BaseComponentDirective implements OnInit {
  seconds = 3;
  redirectUrl: string;

  constructor(
    public readonly store$: Store<State>,
    public readonly route: ActivatedRoute,
    public readonly router: Router,
    public readonly windowRef: WindowRefService,
    public readonly classicRoutesService: ClassicRoutesService,
    public readonly titleService: TitleService,
    public readonly translate: TranslateService
  ) {
    super();
  }

  redirectionMessage(seconds: number): string {
    return this.translate.instant("You will be redirected in {{seconds}} seconds...", { seconds });
  }

  ngOnInit(): void {
    const title = this.translate.instant("Welcome!");
    this.titleService.setTitle(title);
    this.store$.dispatch(new SetBreadcrumb({ breadcrumb: [{ label: "Account" }, { label: title }] }));

    this.redirectUrl = this.route.snapshot.queryParamMap.get("redirectUrl");

    interval(1000)
      .pipe(
        take(this.seconds),
        tap(() => this.seconds--)
      )
      .subscribe(() => {
        if (this.seconds === 0) {
          if (this.redirectUrl) {
            this.router.navigateByUrl(this.redirectUrl);
          } else {
            this.windowRef.nativeWindow.location.assign(this.classicRoutesService.HOME);
          }
        }
      });
  }
}
