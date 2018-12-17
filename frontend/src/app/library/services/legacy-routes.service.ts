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
  RAWDATA_PRIVATE_SHARED_FOLDERS = "/rawdata/privatesharedfolders/";
  RAWDATA_PUBLIC_DATA_POOLS  = "/rawdata/publicdatapools/";
  INBOX = "/messages/inbox/";
  API_KEYS = (profile: UserProfileModel) => `/users/${profile.userObject.username}/apikeys/`;
  SETTINGS = "/profile/edit/basic/";
  LOGOUT = "/accounts/logout/";
  SET_LANGUAGE = (languageCode: string) => `/language/set/${languageCode}/`;
  FORUM_HOME = "/forum/";
  SEARCH = "/search/";
  TOP_PICKS = "/explore/top-picks/";
  IOTD = "/iotd/archive/";
  GROUPS = "/groups/";
  TRENDING_ASTROPHOTOGRAPHERS = "/trending-astrophotographers/";
}
