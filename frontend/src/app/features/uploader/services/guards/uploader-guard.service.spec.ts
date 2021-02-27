import { TestBed } from "@angular/core/testing";
import { RouterStateSnapshot } from "@angular/router";
import { AppModule } from "@app/app.module";
import { PremiumSubscriptionGuardService } from "@shared/services/guards/premium-subscription-guard.service";
import { UltimateSubscriptionGuardService } from "@shared/services/guards/ultimate-subscription-guard.service";
import { MockBuilder } from "ng-mocks";
import { of } from "rxjs";
import { UploaderGuardService } from "./uploader-guard.service";

describe("UploaderGuardService", () => {
  let service: UploaderGuardService;

  beforeEach(async () => {
    await MockBuilder(UploaderGuardService, AppModule)
      .keep(PremiumSubscriptionGuardService)
      .keep(UltimateSubscriptionGuardService);
    service = TestBed.inject(UploaderGuardService);
    jest.spyOn(service.router, "navigateByUrl").mockImplementation(
      () => new Promise<boolean>(resolve => resolve())
    );
  });

  it("should be created", () => {
    expect(service).toBeTruthy();
  });

  it("should pass if user is Premium but not Ultimate", done => {
    jest.spyOn(service.premiumGuard, "canActivate").mockReturnValue(of(true));
    jest.spyOn(service.ultimateGuard, "canActivate").mockReturnValue(of(false));

    service.canActivate(null, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(true);
      done();
    });
  });

  it("should pass if user is Ultimate but not Premium", done => {
    jest.spyOn(service.premiumGuard, "canActivate").mockReturnValue(of(true));
    jest.spyOn(service.ultimateGuard, "canActivate").mockReturnValue(of(false));

    service.canActivate(null, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(true);
      done();
    });
  });

  it("should pass if user is Premium and Ultimate", done => {
    jest.spyOn(service.premiumGuard, "canActivate").mockReturnValue(of(true));
    jest.spyOn(service.ultimateGuard, "canActivate").mockReturnValue(of(true));

    service.canActivate(null, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(true);
      done();
    });
  });

  it("should not pass if user is neither Premium or Ultimate", done => {
    jest.spyOn(service.premiumGuard, "canActivate").mockReturnValue(of(false));
    jest.spyOn(service.ultimateGuard, "canActivate").mockReturnValue(of(false));

    service.canActivate(null, { url: "/foo" } as RouterStateSnapshot).subscribe(result => {
      expect(result).toBe(false);
      done();
    });
  });
});
