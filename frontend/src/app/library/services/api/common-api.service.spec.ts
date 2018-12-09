import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from '@angular/core/testing';
import { of } from "rxjs";
import { UserProfileModel } from "../../models/common/userprofile.model";
import { UserModel } from "../../models/common/user.model";
import { UserSubscriptionModel } from "../../models/common/usersubscription.model";

import { CommonApiService } from './common-api.service';

describe('CommonApiService', () => {
  let service: CommonApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CommonApiService]
    });

    service = TestBed.get(CommonApiService);
    httpMock = TestBed.get(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getUser should work', () => {
    const mockUser = {
      id: 1,
      username: "foo"
    } as UserModel;

    service.getUser(mockUser.id).subscribe(response => {
      expect(response.id).toEqual(mockUser.id);
    });

    const req = httpMock.expectOne(`${service.configUrl}/users/${mockUser.id}`);
    expect(req.request.method).toBe("GET");
    req.flush(mockUser);
  });

  it('getCurrentUserProfile should return the authenticated user', () => {
    const mockUserProfile = {
      user: 1
    } as UserProfileModel;

    service.getCurrentUserProfile().subscribe(response => {
      expect(response.user).toEqual(mockUserProfile.user);
    });

    const req = httpMock.expectOne(`${service.configUrl}/userprofiles/current`);
    expect(req.request.method).toBe("GET");
    req.flush([mockUserProfile]);
  });

  it('getCurrentUserProfile should return null if not authenticated', () => {
    service.getCurrentUserProfile().subscribe(response => {
      expect(response).toEqual(null);
    });

    const req = httpMock.expectOne(`${service.configUrl}/userprofiles/current`);
    expect(req.request.method).toBe("GET");
    req.flush([]);
  });

  it('isAuthenticated should return false if there is no current user profile', () => {
    spyOn(service, 'getCurrentUserProfile').and.returnValue(of(null));
    service.isAuthenticated().subscribe(response => {
      expect(response).toBe(false);
    })
  });

  it('isAuthenticated should return true if there is a current user profile', () => {
    spyOn(service, 'getCurrentUserProfile').and.returnValue(of({user: 1}));
    service.isAuthenticated().subscribe(response => {
      expect(response).toBe(true);
    })
  });

  it('getUserSubscriptions should return list', () => {
    service.getUserSubscriptions().subscribe(response => {
      expect(response.length).toBe(1);
      expect(response[0].user).toBe(1);
    });

    const req = httpMock.expectOne(`${service.configUrl}/usersubscriptions/`);
    expect(req.request.method).toBe("GET");
    req.flush([{user: 1} as UserSubscriptionModel]);
  });

  it('getUserSubscriptions should apply filter', () => {
    service.getUserSubscriptions({id: 1} as UserModel).subscribe(response => {
      expect(response.length).toBe(1);
      expect(response[0].user).toBe(1);
    });

    const req = httpMock.expectOne(`${service.configUrl}/usersubscriptions/?user=1`);
    expect(req.request.method).toBe("GET");
    req.flush([{user: 1} as UserSubscriptionModel]);
  });
});
