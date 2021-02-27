import { TestBed } from "@angular/core/testing";
import { ReactiveFormsModule } from "@angular/forms";
import { AppModule } from "@app/app.module";
import { AppGenerator } from "@app/store/generators/app.generator";
import { appStateEffects, appStateReducers, State } from "@app/store/state";
import { AuthGenerator } from "@features/account/store/auth.generator";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";
import { MockStore, provideMockStore } from "@ngrx/store/testing";
import { MockBuilder, MockRender } from "ng-mocks";
import { LoginFormComponent } from "./login-form.component";

describe("LoginFormComponent", () => {
  let component: LoginFormComponent;
  let store: MockStore;
  const initialState: State = {
    app: AppGenerator.default(),
    auth: AuthGenerator.default()
  };

  beforeEach(() =>
    MockBuilder(LoginFormComponent, AppModule)
      .keep(ReactiveFormsModule)
      .keep(StoreModule.forRoot(appStateReducers))
      .keep(EffectsModule.forRoot(appStateEffects))
      .provide(provideMockStore({ initialState }))
  );

  beforeEach(() => {
    store = TestBed.inject(MockStore);
    component = MockRender(LoginFormComponent).point.componentInstance;
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});
