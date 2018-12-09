import { Injectable } from '@angular/core';
import { UserProfileModel } from "../models/common/userprofile.model";

@Injectable({
  providedIn: 'root'
})
export class LegacyRoutesService {
  HOME = "/";
  LOGIN = "/accounts/login/";
  REGISTER = "/accounts/register/";
  SUBSCRIPTIONS = "/subscriptions/";
  UPLOAD = "/upload/";
  COMMERCIAL_PRODUCTS = (profile: UserProfileModel) => `/users/${profile.userObject.username}/commercial/products/`;
  GALLERY = (profile: UserProfileModel) => `/users/${profile.userObject.username}/`;
  BOOKMARKS = (profile: UserProfileModel) => `/users/${profile.userObject.username}/bookmarks/`;
  PLOTS = (profile: UserProfileModel) => `/users/${profile.userObject.username}/plots/`;
  RAWDATA = "/rawdata/";
}
