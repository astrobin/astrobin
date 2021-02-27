import { RouterModule } from "@angular/router";
import { RouterTestingModule } from "@angular/router/testing";
import { AppComponent } from "@app/app.component";
import { AppModule } from "@app/app.module";
import { initialState } from "@app/store/state";
import { provideMockStore } from "@ngrx/store/testing";
import { MockBuilder, MockRender } from "ng-mocks";

describe("AppComponent", () => {
  beforeEach(() =>
    MockBuilder(AppComponent, AppModule)
      .keep(RouterModule)
      .keep(RouterTestingModule.withRoutes([]))
      .provide(provideMockStore({ initialState }))
  );

  it("should create the app", () => {
    const fixture = MockRender(AppComponent);
    expect(fixture.point.componentInstance).toEqual(jasmine.any(AppComponent));
  });
});
