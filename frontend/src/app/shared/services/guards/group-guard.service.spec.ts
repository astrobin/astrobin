import { TestBed } from "@angular/core/testing";
import { ActivatedRouteSnapshot, RouterStateSnapshot } from "@angular/router";
import { AppModule } from "@app/app.module";
import { initialState } from "@app/store/state";
import { MockStore, provideMockStore } from "@ngrx/store/testing";
import { GroupGuardService } from "@shared/services/guards/group-guard.service";
import { MockBuilder, MockInstance, MockReset, ngMocks } from "ng-mocks";
import { of } from "rxjs";
import { UserGenerator } from "../../generators/user.generator";

describe("GroupGuardService", () => {
  let service: GroupGuardService;
  let route: ActivatedRouteSnapshot;
  let store: MockStore;

  beforeEach(async () => {
    await MockInstance(ActivatedRouteSnapshot, instance => {
      ngMocks.stub(instance, "data", "get");
    });
  });

  afterEach(MockReset);

  beforeEach(async () => {
    await MockBuilder(GroupGuardService, AppModule)
      .mock(ActivatedRouteSnapshot)
      .provide(provideMockStore({ initialState }));

    store = TestBed.inject(MockStore);
    service = TestBed.inject(GroupGuardService);
    route = TestBed.inject(ActivatedRouteSnapshot);

    jest.spyOn(route, "data", "get").mockReturnValue({ group: "Test group" });
    jest.spyOn(service.router, "navigateByUrl").mockImplementation(
      () => new Promise<boolean>(resolve => resolve())
    );
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("should not pass if user is not in the group", done => {
    jest.spyOn(service.authService, "isAuthenticated").mockReturnValue(of(false));

    service.canActivate(route, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(false);
      done();
    });
  });

  it("should pass if user is in the group", done => {
    const user = UserGenerator.user();
    const state = { ...initialState };
    state.auth.user = user;
    store.setState(state);

    route = TestBed.inject(ActivatedRouteSnapshot);
    jest.spyOn(service.authService, "isAuthenticated").mockReturnValue(of(true));

    service.canActivate(route, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(true);
      done();
    });
  });
});
