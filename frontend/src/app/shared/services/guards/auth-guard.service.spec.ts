import { TestBed } from "@angular/core/testing";
import { RouterStateSnapshot } from "@angular/router";
import { AppModule } from "@app/app.module";
import { AuthGuardService } from "@shared/services/guards/auth-guard.service";
import { MockBuilder } from "ng-mocks";
import { of } from "rxjs";

describe("AuthGuardService", () => {
  let service: AuthGuardService;

  beforeEach(() => MockBuilder(AuthGuardService, AppModule));

  beforeEach(() => {
    service = TestBed.inject(AuthGuardService);
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("should pass if user is authenticated", () => {
    jest.spyOn(service.authService, "isAuthenticated").mockReturnValue(of(true));
    service.canActivate(null, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(true);
    });
  });

  it("should redirect to login page if user is not authenticated", () => {
    jest.spyOn(service.authService, "isAuthenticated").mockReturnValue(of(false));
    jest.spyOn(service.router, "navigateByUrl").mockImplementation(() => {
      return new Promise(resolve => resolve());
    });
    service.canActivate(null, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(false);
      expect(service.router.navigateByUrl).toHaveBeenCalled();
    });
  });
});
