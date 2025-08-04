// Type declarations for modules without TypeScript support

declare module 'react-native' {
  export const View: any;
  export const Text: any;
  export const StyleSheet: any;
  export const ScrollView: any;
  export const TouchableOpacity: any;
  export const Alert: any;
  export const TextInput: any;
  export const RefreshControl: any;
  export const Dimensions: any;
  export const Platform: any;
  export const KeyboardAvoidingView: any;
}

declare module '@react-native-async-storage/async-storage' {
  export default class AsyncStorage {
    static getItem(key: string): Promise<string | null>;
    static setItem(key: string, value: string): Promise<void>;
    static removeItem(key: string): Promise<void>;
    static clear(): Promise<void>;
    static getAllKeys(): Promise<readonly string[]>;
    static multiGet(keys: readonly string[]): Promise<readonly [string, string | null][]>;
    static multiSet(keyValuePairs: readonly [string, string][]): Promise<void>;
    static multiRemove(keys: readonly string[]): Promise<void>;
  }
}

declare module '@expo/vector-icons' {
  import { ComponentType } from 'react';

  interface IconProps {
    name: string;
    size?: number;
    color?: string;
  }

  export const Ionicons: ComponentType<IconProps>;
  export const MaterialIcons: ComponentType<IconProps>;
  export const FontAwesome: ComponentType<IconProps>;
  export const Feather: ComponentType<IconProps>;
}

declare module '@react-navigation/native' {
  export const NavigationContainer: any;
  export const useNavigation: any;
  export const useFocusEffect: any;
}

declare module '@react-navigation/native-stack' {
  export const createNativeStackNavigator: any;
}

declare module '@react-navigation/bottom-tabs' {
  export const createBottomTabNavigator: any;
}

declare module 'expo-secure-store' {
  export const setItemAsync: (key: string, value: string) => Promise<void>;
  export const getItemAsync: (key: string) => Promise<string | null>;
  export const deleteItemAsync: (key: string) => Promise<void>;
}

declare module 'react-native-paper' {
  export const Provider: any;
  export const Button: any;
  export const Card: any;
  export const Title: any;
  export const Paragraph: any;
}
